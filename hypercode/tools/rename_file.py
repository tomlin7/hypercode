
import os
from langchain_core.tools import tool

@tool
def rename_file(old_path: str, new_path: str) -> str:
    """Renames a file or folder."""
    os.rename(old_path, new_path)
    return f"Successfully renamed {old_path} to {new_path}"
