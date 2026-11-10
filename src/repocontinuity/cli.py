"""Explicit-command CLI: no automatic monitoring, modifications or network access."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
import shutil
import sys

from . import __version__
from .gitinfo import git_root
from .storage import db_path, init_state, schema_version, SCHEMA_VERSION


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="repocontinuity",
        description="Local-first, evidence-aware AI project handoff foundation",
    )
    parser.add_argument("--version", action="version", version=f"RepoContinuity {__version__}")
    subcommands = parser.add_subparsers(dest="command", required=True)
    doctor = subcommands.add_parser("doctor", help="Read-only diagnostics (JSON)")
    doctor.add_argument("--root", type=Path, default=Path.cwd(), help="Repository path")
    initialize = subcommands.add_parser("init", help="Create local SQLite project state")
    initialize.add_argument("--root", type=Path, default=Path.cwd(), help="Repository path")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = create_parser().parse_args(argv)
    supplied_root = args.root.expanduser().resolve()
    root = git_root(supplied_root)
    if args.command == "doctor":
        path = db_path(root) if root else None
        version = None
        warning = None
        if (path is not None and not path.parent.is_symlink()
                and path.is_file() and not path.is_symlink()):
            try:
                version = schema_version(path)
            except (ValueError, OSError, sqlite3.DatabaseError) as exc:
                warning = f"State database could not be inspected: {type(exc).__name__}"
        report = {
            "tool_version": __version__,
            "python_supported": sys.version_info >= (3, 11),
            "git_available": shutil.which("git") is not None,
            "git_repository": root is not None,
            "initialized": version == SCHEMA_VERSION,
            "schema_version": version,
        }
        if warning:
            report["warning"] = warning
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    if args.command == "init":
        if root is None:
            print("Error: provide a directory inside a Git repository.", file=sys.stderr)
            return 2
        try:
            _, created = init_state(root)
        except (OSError, ValueError, sqlite3.DatabaseError) as exc:
            print(f"Error: initialization failed ({type(exc).__name__}): {exc}", file=sys.stderr)
            return 1
        print("Initialized local project state." if created else "Project state already initialized.")
        return 0
    return 2
