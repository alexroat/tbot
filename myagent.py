import inspect
import json
import os
import asyncio
import time
from typing import Callable, Dict, Any, List
from dotenv import load_dotenv
from openai import OpenAI

# Load configuration from .env file
load_dotenv()

def generate_tool_schema(func: Callable) -> Dict[str, Any]:
    """
    Generates an OpenAI/DeepSeek compatible JSON schema from a Python function
    using reflection and type hints.
    """
    name = func.__name__
    doc = func.__doc__ or "No description provided."
    description = doc.split("\n")[0].strip()
    
    signature = inspect.signature(func)
    properties = {}
    required = []

    type_mapping = {
        int: "integer", str: "string", float: "number", 
        bool: "boolean", list: "array", dict: "object"
    }

    for param_name, param in signature.parameters.items():
        if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            continue
        param_type = type_mapping.get(param.annotation, "string")
        properties[param_name] = {
            "type": param_type,
            "description": f"The {param_name} parameter."
        }
        if param.default == inspect.Parameter.empty:
            required.append(param_name)

    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
    }


class Agent:
    def __init__(self, system_prompt: str = "You are a helpful autonomous agent."):
        self.tool_map: Dict[str, Callable] = {}
        self.tool_metadata: Dict[str, Dict[str, Any]] = {}
        self.tools_schemas: List[Dict[str, Any]] = []
        self.system_prompt = system_prompt
        self.memory: List[Dict[str, Any]] = []
        
        # Performance and budget tracking
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_wait_time = 0.0 # Time spent waiting for human input
        
        # Configuration setup fetched from environment
        self.client = OpenAI(
            base_url=os.getenv("LLM_PROVIDER_URL", "https://api.openai.com/v1"),
            api_key=os.getenv("LLM_API_KEY")
        )
        self.model_name = os.getenv("LLM_MODEL_NAME", "o4-mini")

    def add_tool(self, tool: Callable, requires_consent: bool = False):
        """Registers a tool and builds schema with consent metadata."""
        name = tool.__name__
        if name not in self.tool_map:
            self.tool_map[name] = tool
            self.tool_metadata[name] = {"requires_consent": requires_consent}
            self.tools_schemas.append(generate_tool_schema(tool))
            print(f"[Agent] Registered tool: {name} (Consent: {requires_consent})")

    async def ask_user_permission(self, tool_name: str, args: Dict[str, Any]) -> bool:
        """Helper function to prompt the user for confirmation in the terminal, tracking wait time."""
        print(f"\n⚠️  [PERMISSION REQUIRED] The agent wants to execute: '{tool_name}' with args: {args}")
        loop = asyncio.get_running_loop()
        
        wait_start = time.time()
        try:
            user_response = await loop.run_in_executor(
                None, 
                lambda: input("Allow this action? (y/n): ").strip().lower()
            )
        except (KeyboardInterrupt, EOFError):
            print("\n❌ Permission denied due to user interruption.")
            return False
        finally:
            self.total_wait_time += (time.time() - wait_start)
            
        return user_response in ['y', 'yes']

    async def _execute_single_tool(self, tool_call) -> Dict[str, Any]:
        """Executes a single tool dynamically, utilizing thread-pooling for synchronous functions."""
        tool_name = tool_call.function.name
        tool_args = json.loads(tool_call.function.arguments)
        loop = asyncio.get_running_loop()

        print(f"🤖 [Agent Worker] Processing: '{tool_name}' with args: {tool_args}")
        
        if tool_name not in self.tool_map:
            return {
                "tool_call_id": tool_call.id, 
                "role": "tool", 
                "name": tool_name, 
                "content": json.dumps({"error": f"Tool '{tool_name}' not found."})
            }

        # Check for user consent if required
        if self.tool_metadata.get(tool_name, {}).get("requires_consent", False):
            approved = await self.ask_user_permission(tool_name, tool_args)
            if not approved:
                print(f"❌ [Permission Denied] User blocked execution of: {tool_name}")
                return {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": tool_name,
                    "content": json.dumps({"error": "User denied permission to execute this tool."})
                }

        target_tool = self.tool_map[tool_name]
        try:
            # Native inspection mapping compliant with Python 3.14+
            if inspect.iscoroutinefunction(target_tool):
                output = await target_tool(**tool_args)
            else:
                output = await loop.run_in_executor(None, lambda: target_tool(**tool_args))
        except Exception as e:
            output = json.dumps({"error": f"Execution failed: {str(e)}"})

        return {
            "tool_call_id": tool_call.id,
            "role": "tool",
            "name": tool_name,
            "content": output
        }

    async def _compress_memory(self):
        """Reduces historical memory bloat using a consolidation prompt layout."""
        print("🧹 [Memory Guard] Compressing context window...")
        loop = asyncio.get_running_loop()
        
        # Ensure conversation_history is serializable (converting objects to dicts if needed)
        conversation_history = []
        for m in self.memory:
            if hasattr(m, "role"): # It's a message object
                if m.role == "system": continue
                msg_dict = {"role": m.role, "content": m.content}
                if hasattr(m, "tool_calls") and m.tool_calls:
                    msg_dict["tool_calls"] = [
                        {"id": tc.id, "type": tc.type, "function": {"name": tc.function.name, "arguments": tc.function.arguments}} 
                        for tc in m.tool_calls
                    ]
                conversation_history.append(msg_dict)
            else: # It's already a dict
                if m.get("role") == "system": continue
                conversation_history.append(m)
        
        compression_prompt = [
            {"role": "system", "content": "Summarize the essential facts and core metrics discovered so far. Keep it ultra-short."},
            {"role": "user", "content": f"Compress this log: {json.dumps(conversation_history)}"}
        ]
        
        response = await loop.run_in_executor(
            None,
            lambda: self.client.chat.completions.create(
                model=self.model_name,
                messages=compression_prompt
            )
        )
        
        summary = response.choices[0].message.content
        self.memory = [
            {"role": "system", "content": self.system_prompt},
            {"role": "system", "content": f"Summary of previous actions: {summary}"}
        ]
        print("🧹 [Memory Guard] Compression finalized.")

    async def execute(self, user_message: str, max_iterations: int = 5, max_tokens: int = 20000, max_seconds: float = 30.0, reset_memory: bool = False) -> str:
        """Runs the ReAct loop tracking active execution times, token budgets and iteration scales."""
        print(f"\n🚀 [Agent] Starting self-regulating task: '{user_message}'")
        
        start_time = time.time()
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.total_wait_time = 0.0 # Reset wait time for each task
        
        if reset_memory or not self.memory:
            self.memory = [{"role": "system", "content": self.system_prompt}]
        
        self.memory.append({"role": "user", "content": user_message})

        for iteration in range(1, max_iterations + 1):
            # Calculate elapsed time excluding wait time
            elapsed_time = (time.time() - start_time) - self.total_wait_time
            accumulated_tokens = self.total_prompt_tokens + self.total_completion_tokens
            
            print(f"\n--- [Loop Check] Iteration {iteration}/{max_iterations} | Active Time: {elapsed_time:.1f}s/{max_seconds}s | Tokens: {accumulated_tokens}/{max_tokens} ---")

            # Boundary safety guards check
            if elapsed_time >= max_seconds:
                print("⚠️ [Safety Trigger] Execution halted: Time budget exhausted.")
                return "Task aborted due to execution timeout limitations."
                
            if accumulated_tokens >= max_tokens:
                print("⚠️ [Safety Trigger] Execution halted: Token budget exhausted.")
                return "Task aborted due to safety token budget exhaustion."

            if len(self.memory) > 12:
                await self._compress_memory()

            # Dynamic notice payload injection
            boundary_warning = (
                f"\n[RESOURCE CONTEXT: Iteration {iteration}/{max_iterations} | "
                f"Elapsed Time: {elapsed_time:.1f}s limit: {max_seconds}s | "
                f"Consumed Tokens: {accumulated_tokens} limit: {max_tokens}.\n"
                f"Be strategic. Batch calls if needed. If thresholds are close, wrap up execution and output the final text answer immediately!]"
            )
            
            self.memory[-1]["content"] += boundary_warning

            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.client.chat.completions.create(
                    model=self.model_name,
                    messages=self.memory,
                    tools=self.tools_schemas if self.tools_schemas else None,
                    tool_choice="auto" if self.tools_schemas else None
                )
            )

            # Strip notice out to preserve clean history state
            self.memory[-1]["content"] = self.memory[-1]["content"].split("\n[RESOURCE CONTEXT")[0]

            # Collect active token metrics logs
            if response.usage:
                self.total_prompt_tokens += response.usage.prompt_tokens
                self.total_completion_tokens += response.usage.completion_tokens
                print(f"📊 [Token Metrics] Step Use -> Input: {response.usage.prompt_tokens} | Output: {response.usage.completion_tokens}")

            response_message = response.choices[0].message
            self.memory.append(response_message)

            # Exit check condition
            if not response_message.tool_calls:
                total_final_tokens = self.total_prompt_tokens + self.total_completion_tokens
                print(f"✅ [Agent] Finished. Final Stats -> Total Time: {time.time() - start_time:.1f}s | Total Tokens: {total_final_tokens}")
                return response_message.content or ""

            print(f"📊 [Agent] LLM scheduled {len(response_message.tool_calls)} actions to run concurrently.")
            
            # Batch execution processing definitions
            tasks = [self._execute_single_tool(call) for call in response_message.tool_calls]
            
            # FIXED: Directly awaiting the gather future to avoid event-loop TypeErrors
            tool_results = await asyncio.gather(*tasks)
            
            for result_message in tool_results:
                self.memory.append(result_message)
                
        print("⚠️ [Safety Trigger] Execution halted: Maximum iterations reached.")
        return "Task stopped: Reached max iteration limits."

