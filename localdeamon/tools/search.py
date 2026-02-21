import subprocess
from pathlib import Path
from localdeamon.tool_registry import tool


@tool
def search(query: str) -> str:
    """
    Search the web for a query string.

    Args:
        query: Search query string

    Returns:
        Search results
    """
    try:
        script_path = Path(__file__).resolve().parent.parent.parent / "tools" / "web_search.sh"

        if not script_path.exists():
            return f"Error: Script not found at {script_path}"

        result = subprocess.run(
            [str(script_path), query],
            capture_output=True,
            text=True,
            timeout=60,
            cwd=Path.cwd()
        )

        output = []
        if result.stdout:
            output.append(result.stdout)
        if result.stderr:
            output.append(f"[stderr]: {result.stderr}")
        if result.returncode != 0:
            output.append(f"[exit code: {result.returncode}]")

        return "\n".join(output) if output else "[no output]"

    except subprocess.TimeoutExpired:
        return f"Error: Search timed out after 60 seconds"
    except Exception as e:
        return f"Error performing search: {e}"
