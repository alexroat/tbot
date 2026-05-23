# Autonomous AI Agent (tbot)

This project implements an autonomous AI agent in Python that can interact with the local file system and execute shell commands. It uses a modular tool-based approach to perform actions directly (e.g., reading/writing files, running commands) rather than merely describing them. The agent is defined in `myagent.py`, and the main entrypoint script is `second.py`.

## Features

- **Tool Registration and Schema Generation**: Automatically generates JSON schemas for tools based on Python function signatures (`myagent.py`).
- **User Consent Workflow**: Prompts the user for permission before executing potentially destructive tools (write, delete, shell commands).
- **Built-in Tools**: 
  - list_directory_contents  – Lists files and directories.
  - read_file_content       – Reads and returns file contents.
  - write_file_content      – Creates or overwrites files.
  - delete_file             – Deletes files.
  - run_shell_command       – Executes arbitrary shell commands.
- **Safety and Budget Guards**: Enforces time, token, and iteration limits on agent executions, with automatic memory compression.
- **Interactive CLI**: Launch an interactive session to issue natural-language commands to the agent.

## Installation

1. Clone the repository:

   ```bash
   git clone git@github.com:alexroat/tbot.git
   cd tbot
   ```
2. (Optional) Create and activate a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file in the project root with the following variables:

   ```ini
   LLM_API_KEY=your_openai_api_key
   LLM_PROVIDER_URL=https://api.openai.com/v1
   LLM_MODEL_NAME=o4-mini
   ```

## Usage

Run the main agent script:

```bash
python second.py
```

- The agent will register its tools and start an interactive REPL.
- Type natural-language commands (e.g., "Create a file named example.txt with content 'Hello'"), and the agent will perform the appropriate actions.
- To exit, type `exit` or `quit`.

## Project Structure

```
├── myagent.py        # Core Agent implementation & tool management
├── second.py         # Main CLI entrypoint and tool definitions
├── requirements.txt  # Python dependencies
├── .env              # Environment variables (not committed)
├── README.md         # Project documentation
└── ...               # Other supporting files
```

## Contributing

Contributions welcome! Please open issues or pull requests for new features or bug fixes.

## License

MIT License