
import shutil
from langchain_core.tools import tool

@tool
def move_file(source_path: str, destination_path: str) -> str:
    """Moves a file or folder."""
    shutil.move(source_path, destination_path)
    return f"Successfully moved {source_path} to {destination_path}"
