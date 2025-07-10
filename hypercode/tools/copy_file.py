
import shutil
from langchain_core.tools import tool

@tool
def copy_file(source_path: str, destination_path: str) -> str:
    """Copies a file or folder."""
    shutil.copy(source_path, destination_path)
    return f"Successfully copied {source_path} to {destination_path}"
