from pathlib import Path
from localdeamon.tool_registry import tool


@tool
def write(file_path: str, content: str) -> str:
    """
    Write content to a file.

    Args:
        file_path: Path to the file to write
        content: Content to write to the file

    Returns:
        Success message or error description
    """
    try:
        path = Path(file_path)

        if path.exists() and not path.is_file():
            return f"Error: '{file_path}' exists but is not a file"

        path.parent.mkdir(parents=True, exist_ok=True)

        path.write_text(content, encoding='utf-8')

        size = path.stat().st_size
        lines = content.count('\n') + 1
        return f"Successfully wrote {size} bytes ({lines} lines) to '{file_path}'"

    except PermissionError:
        return f"Error: Permission denied writing to '{file_path}'"
    except Exception as e:
        return f"Error writing file: {e}"
