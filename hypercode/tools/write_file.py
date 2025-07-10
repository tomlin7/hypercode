
from langchain_core.tools import tool

@tool
def write_file(file_path: str, content: str) -> str:
    """Writes content to a file. Creates the file if it doesn't exist."""
    with open(file_path, "w") as f:
        f.write(content)
    return f"Successfully wrote to {file_path}"
