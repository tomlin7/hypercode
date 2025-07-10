
import os
from langchain_core.tools import tool

@tool
def create_folder(folder_path: str) -> str:
    """Creates a new folder."""
    os.makedirs(folder_path, exist_ok=True)
    return f"Successfully created folder: {folder_path}"
