

import subprocess
from langchain_core.tools import tool

@tool
def run_cli_command(command: str) -> str:
    """Runs a command in the command line."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    except Exception as e:
        return f"An error occurred: {e}"

