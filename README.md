# HyperCode

Hyper coding agent in an interactive super TUI.

## Quick Start

```bash
pip install -e .
```
```bash
GOOGLE_API_KEY=your_api_key_here
```

### TUI

```bash
python -m hypercode
```

- `Ctrl+Q` once: Interrupt current task
- `Ctrl+Q` twice (within 2s): Exit application
- `Ctrl+C`: Interrupt current task

#### CLI

```bash
python -m hypercode.main "create a python file to calculate fibonacci numbers"
```

## Architecture

```
┌──────────────────────────────────┐
│         ReAct Agent              │
│                                  │
│  ┌────────┐  ┌────────┐  ┌──────┐│
│  │ THINK  │→ │  ACT   │→ │ OBS  ││
│  │Analyze │  │Execute │  │Check ││
│  │& Plan  │  │Tools   │  │Result││
│  └────────┘  └────────┘  └──────┘│
│       ↑                      │   │
│       └──────────────────────┘   │
└──────────────────────────────────┘

Tools:
- read_file
- write_file
- create_folder
- run_command
```
