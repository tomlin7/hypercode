

import os
import re
from langchain_core.tools import tool

@tool
def grep(directory: str, pattern: str) -> str:
    """Greps for a pattern in all files in a directory."""
    results = []
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            with open(file_path, "r", errors="ignore") as f:
                for i, line in enumerate(f, 1):
                    if re.search(pattern, line):
                        results.append(f"{file_path}:{i}:{line.strip()}")
    return "\n".join(results)

