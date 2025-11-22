import os
import subprocess
from pathlib import Path
from typing import Any, Dict

from langchain_core.tools import tool


@tool
def read_file(file_path: str) -> Dict[str, Any]:
    """Read the contents of a file.
    
    Args:
        file_path: Path to the file to read
        
    Returns:
        Dictionary with 'success', 'content', and optional 'error' keys
    """
    try:
        path = Path(file_path).resolve()
        if not path.exists():
            return {
                "success": False,
                "error": f"File not found: {file_path}"
            }
        
        content = path.read_text(encoding='utf-8')
        return {
            "success": True,
            "content": content,
            "path": str(path)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error reading file: {str(e)}"
        }


@tool
def write_file(file_path: str, content: str) -> Dict[str, Any]:
    """Write content to a file. Creates the file if it doesn't exist.
    
    Args:
        file_path: Path to the file to write
        content: Content to write to the file
        
    Returns:
        Dictionary with 'success', 'path', and optional 'error' keys
    """
    try:
        path = Path(file_path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        is_new = not path.exists()
        
        path.write_text(content, encoding='utf-8')
        return {
            "success": True,
            "path": str(path),
            "action": "created" if is_new else "modified"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error writing file: {str(e)}"
        }


@tool
def create_folder(folder_path: str) -> Dict[str, Any]:
    """Create a folder/directory. Creates parent directories as needed.
    
    Args:
        folder_path: Path to the folder to create
        
    Returns:
        Dictionary with 'success', 'path', and optional 'error' keys
    """
    try:
        path = Path(folder_path).resolve()
        path.mkdir(parents=True, exist_ok=True)
        return {
            "success": True,
            "path": str(path)
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error creating folder: {str(e)}"
        }


@tool
def run_command(command: str, cwd: str = ".") -> Dict[str, Any]:
    """Run a shell command and return the output.
    
    Args:
        command: The command to execute
        cwd: Working directory for the command (default: current directory)
        
    Returns:
        Dictionary with 'success', 'stdout', 'stderr', 'return_code' keys
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30  # 30 second
        )
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode,
            "command": command
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Command timed out after 30 seconds"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error running command: {str(e)}"
        }


ALL_TOOLS = [read_file, write_file, create_folder, run_command]
