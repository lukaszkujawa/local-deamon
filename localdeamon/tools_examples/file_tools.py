"""File operation tools"""
from pathlib import Path
from localdeamon.tool_registry import tool


@tool
def list_files(directory: str) -> str:
    """List all files in a directory"""
    try:
        path = Path(directory)
        files = [f.name for f in path.iterdir() if f.is_file()]
        return f"Files in {directory}: {', '.join(files)}"
    except Exception as e:
        return f"Error: {e}"


@tool
def file_size(file_path: str) -> str:
    """Get the size of a file in bytes"""
    try:
        size = Path(file_path).stat().st_size
        return f"{file_path}: {size} bytes"
    except Exception as e:
        return f"Error: {e}"
