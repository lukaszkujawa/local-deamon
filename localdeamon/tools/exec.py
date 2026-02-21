import subprocess
from pathlib import Path
from localdeamon.tool_registry import tool


@tool
def exec(command: str) -> str:
    """
    Execute a shell command and return output.

    Args:
        command: Shell command to execute

    Returns:
        Command output (stdout + stderr)
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
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
        return f"Error: Command timed out after 30 seconds"
    except Exception as e:
        return f"Error executing command: {e}"
