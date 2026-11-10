"""Read-only Git metadata helpers. No shell interpolation or network calls."""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess


def git_root(path: Path) -> Path | None:
    if not path.is_dir() or not shutil.which("git"):
        return None
    try:
        result = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0 or not result.stdout.strip():
        return None
    return Path(result.stdout.strip()).resolve()
