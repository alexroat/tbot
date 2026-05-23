import os
import json
import asyncio
from myagent import Agent

# =====================================================================
# SYSTEM OPERATIONAL TOOLS (Expanded)
# =====================================================================

async def list_directory_contents() -> str:
    """List all files and directories in the current working path."""
    try:
        files = os.listdir('.')
        return json.dumps({"current_directory": os.getcwd(), "files": files})
    except Exception as e:
        return json.dumps({"error": f"Failed to list directory: {str(e)}"})


async def read_file_content(file_path: str) -> str:
    """Read and return the plain text content of a specific file."""
    try:
        if not os.path.exists(file_path):
            return json.dumps({"error": f"File '{file_path}' does not exist."})
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return json.dumps({"file": file_path, "content": content})
    except Exception as e:
        return json.dumps({"error": f"Failed to read file {file_path}: {str(e)}"})


async def write_file_content(file_path: str, content: str) -> str:
    """Create or overwrite a file with specific text content."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"💾 [Disk I/O] Successfully wrote file to: {file_path}")
        return json.dumps({"status": "success", "file": file_path, "bytes_written": len(content)})
    except Exception as e:
        return json.dumps({"error": f"Failed to write file {file_path}: {str(e)}"})


async def delete_file(file_path: str) -> str:
    """Delete a file from the file system."""
    try:
        if not os.path.exists(file_path):
            return json.dumps({"error": f"File '{file_path}' not found."})
        os.remove(file_path)
        print(f"🗑️ [Disk I/O] Deleted file: {file_path}")
        return json.dumps({"status": "success", "message": f"File '{file_path}' deleted."})
    except Exception as e:
        return json.dumps({"error": f"Failed to delete file {file_path}: {str(e)}"})


async def run_shell_command(command: str) -> str:
    """Execute a general shell command and return its output."""
    print(f"⚙️  [Shell] Executing command: {command}")
    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        return json.dumps({
            "status": "executed",
            "return_code": process.returncode,
            "stdout": stdout.decode('utf-8', errors='ignore'),
            "stderr": stderr.decode('utf-8', errors='ignore')
        })
    except Exception as e:
        return json.dumps({"error": f"Command execution failed: {str(e)}"})


# =====================================================================
# MAIN AUTOMATION WORKFLOW
# =====================================================================

async def main():
    workspace_bot = Agent(
        system_prompt=(
            "You are an autonomous AI Agent with direct access to the local file system and shell. "
            "Your primary goal is to PERFORM actions, not just talk about them. "
            "If a user asks for a script, a file, or an investigation, do NOT just show the code in chat. "
            "Instead, immediately use 'write_file_content' to create the file and 'list_directory_contents' or 'read_file_content' to explore. "
            "You have tools for a reason: USE THEM as your first response to any task. "
            "Always prefer acting (tool calls) over explaining (text). "
            "To execute scripts or general commands, use 'run_shell_command'."
        )
    )
    
    workspace_bot.add_tool(list_directory_contents)
    workspace_bot.add_tool(read_file_content)
    workspace_bot.add_tool(write_file_content, requires_consent=True)
    workspace_bot.add_tool(delete_file, requires_consent=True)
    workspace_bot.add_tool(run_shell_command, requires_consent=True)
    
    print("\n🤖 [Agent] Workspace Bot is ready with full Shell access!")
    print("Type 'exit' or 'quit' to stop.")

    while True:
        try:
            loop = asyncio.get_running_loop()
            user_input = await loop.run_in_executor(None, lambda: input("\n👤 [User]: "))
            if user_input.lower() in ['exit', 'quit']: break
            if not user_input.strip(): continue

            final_report = await workspace_bot.execute(user_message=user_input, max_iterations=7)
            print(f"\n🎯 [Agent Response]:\n{final_report}")
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error during execution: {e}")

if __name__ == "__main__":
    asyncio.run(main())