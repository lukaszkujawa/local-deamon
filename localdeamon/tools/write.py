import json
from pathlib import Path
from typing import Union, Dict, List, Any
from localdeamon.tool_registry import tool


@tool
def write(file_path: str, content: Union[str, Dict[str, Any], List[Any]]) -> str:
    """
    Write content to a file. Creates parent directories if needed.

    Args:
        file_path: Path to the file to write
        content: Content to write (string, dict, or list). Dicts/lists auto-convert to JSON.

    Returns:
        Success message or error description
    """
    try:
        was_dict_or_list = isinstance(content, (dict, list))
        if was_dict_or_list:
            content = json.dumps(content, indent=2, ensure_ascii=False)

        path = Path(file_path)

        if path.exists() and not path.is_file():
            return f"Error: '{file_path}' exists but is not a file"

        path.parent.mkdir(parents=True, exist_ok=True)

        path.write_text(content, encoding='utf-8')

        size = path.stat().st_size
        lines = content.count('\n') + 1

        suffix = " (auto-converted from dict/list to JSON)" if was_dict_or_list else ""
        return f"Successfully wrote {size} bytes ({lines} lines) to '{file_path}'{suffix}"

    except PermissionError:
        return f"Error: Permission denied writing to '{file_path}'"
    except Exception as e:
        return f"Error writing file: {e}"
