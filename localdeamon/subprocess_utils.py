
import subprocess
from pathlib import Path
from typing import List


def run_command(cmd: List[str], timeout: int = 30) -> str:
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
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
