
from langchain_core.tools import tool

@tool
def read_file(file_path: str) -> str:
    """Reads the contents of a file."""
    with open(file_path, "r") as f:
        return f.read()
