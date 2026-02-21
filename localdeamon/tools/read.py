from pathlib import Path
from localdeamon.tool_registry import tool


@tool
def read(file_path: str) -> str:
    """
    Read and return contents of a text file.

    Args:
        file_path: Path to the file to read

    Returns:
        File contents as string
    """
    try:
        path = Path(file_path)

        if not path.exists():
            return f"Error: File '{file_path}' not found"

        if not path.is_file():
            return f"Error: '{file_path}' is not a file"

        max_size = 10 * 1024 * 1024
        if path.stat().st_size > max_size:
            return f"Error: File too large (max 10MB). File size: {path.stat().st_size / 1024 / 1024:.2f}MB"

        try:
            content = path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            try:
                content = path.read_text(encoding='latin-1')
            except Exception as e:
                return f"Error: Could not decode file (binary file?): {e}"

        return content

    except PermissionError:
        return f"Error: Permission denied reading '{file_path}'"
    except Exception as e:
        return f"Error reading file: {e}"
