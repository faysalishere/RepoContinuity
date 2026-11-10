"""Read-only Git metadata helpers. No shell interpolation or network calls."""
from __future__ import annotations

from pathlib import Path
import shutil
import subprocess


def _git(path: Path, *args: str) -> str:
    command = ["git", "-C", str(path), *args]
    try:
        result = subprocess.run(command, capture_output=True, check=False, timeout=8)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ValueError(f"Git not accessible: {type(exc).__name__}") from exc
    if result.returncode != 0:
        raise ValueError("Git command failed; repository may have no commits")
    return result.stdout.decode("utf-8", "replace").strip()


def git_root(path: Path) -> Path | None:
    if not path.is_dir() or not shutil.which("git"):
        return None
    try:
        return Path(_git(path, "rev-parse", "--show-toplevel")).resolve()
    except ValueError:
        return None


def git_snapshot(root: Path) -> dict:
    """Observe HEAD and both tracked/untracked dirt without capturing file names."""
    sha_before = _git(root, "rev-parse", "HEAD")
    # Exclude RepoContinuity's private state even when an older nested
    # .gitignore made its own ignore file visible to Git.
    porcelain = _git(root, "status", "--porcelain=v1", "--untracked-files=normal", "--", ".", ":(exclude).repocontinuity")
    staged = _git(root, "diff", "--cached", "--name-only", "--", ".", ":(exclude).repocontinuity")
    branch = _git(root, "branch", "--show-current")
    sha_after = _git(root, "rev-parse", "HEAD")
    if sha_before != sha_after:
        raise ValueError("Git HEAD changed during checkpoint capture")
    if not (len(sha_before) in (40, 64) and all(ch in "0123456789abcdef" for ch in sha_before)):
        raise ValueError("Unexpected Git commit identifier")
    return {"commit_sha": sha_before, "worktree_dirty": bool(porcelain), "staged_dirty": bool(staged), "branch": branch or None}
