
from langchain_core.tools import tool

@tool
def read_file_range(file_path: str, start: int, end: int) -> str:
    """Reads a specific range of lines from a file."""
    with open(file_path, "r") as f:
        lines = f.readlines()
    return "".join(lines[start:end])
