# TBot

TBot is an autonomous AI agent framework and associated tooling designed for experimentation with agent-based file system and shell command interactions. This repository includes:

- **myagent.py**: A tool-based AI agent with built-in safety checks, consent handling, and memory compression. It can interact with local files and execute shell commands based on defined tools.
- **second.py**: A command-line interface (CLI) utility exposing core file operations (list, read, write, delete) and shell command execution. Useful for manual or scripted file-system interactions.
- **get_quotes.py**: A small script to fetch random quotes from a local `quotes.csv` database.
- **quotes.csv**: A CSV file containing sample quotes used by `get_quotes.py`.
- **.env**: Environment variable definitions (e.g., API keys or configuration). Make sure to set up required variables before running scripts.
- **requirements.txt**: Python dependencies needed for the project.

## Setup

1. Clone this repository:

   ```bash
   git clone <repo-url>
   cd tbot
   ```

2. Create and activate a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate   # macOS/Linux
   venv\Scripts\activate      # Windows
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:

   Copy `.env.example` to `.env` and update values:

   ```bash
   cp .env.example .env
   # Edit .env with your preferred editor
   ```

## Usage

### Run the AI Agent

```bash
python myagent.py
```

This launches an interactive REPL allowing you to send instructions to the AI agent, which can then perform file operations or shell commands.

### CLI File & Shell Utility

Use `second.py` for quick file system operations:

- List files:  `python second.py list`
- Read file:   `python second.py read <file_path>`
- Write file:  `python second.py write <file_path> <content>`
- Delete file: `python second.py delete <file_path>`
- Shell exec:  `python second.py shell <command>`

### Fetch Random Quotes

```bash
python get_quotes.py
```

Prints a random quote from `quotes.csv`.

## Contributing

Contributions are welcome! Feel free to open issues or pull requests.

## License

This project is licensed under the MIT License.
