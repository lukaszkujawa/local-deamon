import subprocess
from localdeamon.tool_registry import tool
from localdeamon.subprocess_utils import run_command


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
        return run_command(["/bin/sh", "-c", command], timeout=30)
    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after 30 seconds"
    except (OSError, subprocess.SubprocessError) as e:
        return f"Error executing command: {e}"
