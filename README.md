# HyperCode (WIP)

An intelligent multi-agent coding assistant that breaks down complex programming tasks into manageable steps and executes them autonomously.

HyperCode is like having a team of specialized AI developers working together on your coding projects. Instead of just generating code, it plans, codes, tests, and debugs - all while keeping you in control of sensitive operations.

Think of it as your personal coding team that:

- **Plans** your project step-by-step
- **Writes** the actual code
- **Tests** everything thoroughly
- **Debugs** issues automatically
- **Handles** file operations safely

## How It Works

HyperCode uses a multi-agent approach with specialized roles:

### The Orchestrator (Planner)

The mastermind that breaks down your request into actionable steps and coordinates the other agents.

### Coding Agent

Writes clean, functional code based on your requirements.

### Tool Agent

Handles file operations like reading, writing, creating folders, and running commands.

### Testing Agent

Creates and runs tests to ensure your code works correctly.

### Debugging Agent

Analyzes test failures and suggests fixes when things go wrong.

## Installation

```bash
cd hypercode
pip install -e .

GOOGLE_API_KEY=your_google_ai_api_key_here
```

### Basic Usage

```bash
python -m hypercode
```

## Project Structure

```py
hypercode/
├── agents/           # Specialized AI agents
│   ├── orchestrator.py    # Plans and coordinates tasks
│   ├── coding_agent.py    # Writes code
│   ├── tool_agent.py      # Handles file operations
│   ├── testing_agent.py   # Creates and runs tests
│   └── debugging_agent.py # Fixes issues
├── tools/            # Available tools for agents
│   ├── read_file.py       # File reading
│   ├── write_file.py      # File writing
│   ├── create_folder.py   # Directory creation
│   └── ...               # Other utilities
├── graph.py          # Workflow orchestration
└── main.py          # CLI entry point
```

## Contributing

Here's how you can help:

1. **Report Issues**: Found a bug? Open an issue with details
2. **Suggest Features**: Have ideas? We'd love to hear them
3. **Submit PRs**: Code improvements are always welcome
4. **Documentation**: Help improve these docs

## Requirements

- Python 3.12+
- Google AI API key

### Common Issues

**"GOOGLE_API_KEY not set"**

- Make sure your `.env` file exists and contains your API key
- Verify the API key is valid and has the necessary permissions

**"Permission denied" errors**

- Check file permissions in your working directory
- Run with appropriate privileges if needed

**Agent not responding**

- Check your internet connection
- Verify your API key hasn't exceeded rate limits

## License

This project is open source. See the LICENSE file for details.
