"""Review RepoContinuity's real CLI in a disposable Git repository.

No files in the user's current repository are created, touched, or uploaded.
"""
from __future__ import annotations

import argparse
import json
from importlib.util import find_spec
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def run(command: list[str], cwd: Path, *, env: dict[str, str] | None = None) -> str:
    result = subprocess.run(command, cwd=cwd, env=env, text=True,
                            capture_output=True, check=False, timeout=25)
    if result.returncode:
        raise RuntimeError(f"Demo command failed ({command[0]}): {result.stderr.strip()}")
    return result.stdout.strip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Safe, temporary RepoContinuity CLI walkthrough")
    parser.add_argument("--yes", action="store_true", help="Skip prompts (use in CI)")
    args = parser.parse_args(argv)
    root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    # Prefer the actually-installed wheel when present; use checkout source otherwise.
    if find_spec("repocontinuity") is None:
        env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(root / "src"), env.get("PYTHONPATH")]))

    def pause(label: str) -> None:
        print(f"\n{label}")
        if not args.yes and sys.stdin.isatty():
            input("Press Enter to continue...")

    with tempfile.TemporaryDirectory(prefix="repocontinuity-demo-") as directory:
        workspace = Path(directory)
        repo = workspace / "example-project"
        repo.mkdir()
        run(["git", "init", "-q"], repo)
        (repo / "example.txt").write_text("An illustrative, non-production project.\n", encoding="utf-8")
        run(["git", "add", "example.txt"], repo)
        run(["git", "-c", "user.name=Demo User", "-c", "user.email=demo@example.invalid",
             "commit", "-qm", "Add illustrative source"], repo)

        def rc(*parts: str) -> dict:
            output = run([sys.executable, "-m", "repocontinuity", *parts], repo, env=env)
            return json.loads(output)

        pause("Step 1/4: Initialize local SQLite state (temporary repo only).")
        initialized = rc("init")
        assert initialized["schema_version"] == 2

        pause("Step 2/4: Record a proposed decision, then explicitly approve it.")
        decision = rc("decision", "add", "--title", "Preserve existing architecture",
                      "--rationale", "Demo-only decision; no actual project authorization")
        approved = rc("decision", "approve", "--id", decision["id"], "--by", "Demo user")
        assert approved["status"] == "approved"

        pause("Step 3/4: Record a completed-but-UNVERIFIED task and Git checkpoint.")
        task = rc("task", "add", "--title", "Review an example change")
        incomplete = rc("task", "status", "--id", task["id"], "--status", "complete_unverified")
        assert incomplete["status"] == "complete_unverified"
        checkpoint = rc("checkpoint", "capture")
        assert checkpoint["status"] == "unverified"

        pause("Step 4/4: Export portable JSON and run non-executing validation.")
        packet = rc("handoff", "export", "--format", "json")
        exported = workspace / "reviewed-handoff.json"  # Outside the Git repo, no dirty-tree side effect.
        exported.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
        outcome = rc("handoff", "validate", "--file", str(exported))
        assert outcome["valid_structure"] is True
        assert outcome["safe_to_apply_automatically"] is False
        assert outcome["requires_review"] is True
        assert packet["tasks"][0]["status"] == "complete_unverified"
        print("\nDEMO COMPLETE: SQLite + Git checkpoint + approval + JSON handoff + read-only validation.")
        print("Task remains UNVERIFIED. Imported approvals are never automatically trusted.")
        print("This demo used a disposable temporary repository and performed NO network requests.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
