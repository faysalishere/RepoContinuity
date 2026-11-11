"""Offline release preflight. Deliberately does NOT publish or run project hooks."""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys
import tomllib


def run(root: Path) -> list[str]:
    errors: list[str] = []
    required = ["README.md", "LICENSE", "MANIFEST.in", "SECURITY.md", "CHANGELOG.md", "docs/QUICK_START.md",
                "docs/RELEASE_PROCESS.md", "docs/SECURITY_AUDIT.md", "examples/quickstart_demo.py",
                "src/repocontinuity/handoff.py", "src/repocontinuity/storage.py", "tests/test_e2e.py"]
    for name in required:
        if not (root / name).is_file():
            errors.append(f"Missing release file: {name}")
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]
    version = project["version"]
    pkg = (root / "src/repocontinuity/__init__.py").read_text(encoding="utf-8")
    if f'__version__ = "{version}"' not in pkg:
        errors.append("pyproject.toml and __init__.__version__ disagree")
    if not re.fullmatch(r"\d+\.\d+\.\d+(?:a\d+|b\d+|rc\d+)?", version):
        errors.append("Version must use supported Python release numbering")
    skills = sorted((root / "skills").glob("*/SKILL.md"))
    if len(skills) != 5:
        errors.append(f"Expected 5 reusable skills, found {len(skills)}")
    for skill in skills:
        data = skill.read_text(encoding="utf-8")
        if not data.startswith("---\n") or not re.search(r"(?m)^name:\s*", data) or not re.search(r"(?m)^description:\s*", data):
            errors.append(f"Invalid skill frontmatter: {skill.relative_to(root)}")
    for file in root.rglob("*"):
        if not file.is_file() or any(x in {".git", ".repocontinuity", "__pycache__", ".venv", "build", "dist"} for x in file.relative_to(root).parts):
            continue
        relative = file.relative_to(root).as_posix()
        if relative.startswith(".env") or relative.endswith((".sqlite3", ".db", ".pem", ".key", ".pyc")):
            errors.append(f"Sensitive/unexpected release file: {relative}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="RepoContinuity offline release checks")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = run(args.root.resolve())
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        return 1
    print("Release checks passed: versions, required docs, five skills, excluded files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
