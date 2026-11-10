"""Explicit, local CLI for memory, Git checkpoints and observed test evidence."""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
import shutil
import sys

from . import __version__
from .gitinfo import git_root
from .memory import checkpoint_action, decision_action, evidence_action, task_action, TASK_STATUSES
from .storage import db_path, init_state, migrate_state, schema_version, SCHEMA_VERSION


def _root(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Git repository path")


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="repocontinuity", description="Local, approval-aware project state")
    parser.add_argument("--version", action="version", version=f"RepoContinuity {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)
    for cmd, detail in (("doctor", "Read-only project diagnostics"),
                        ("init", "Initialize a new SQLite v2 project state"),
                        ("migrate", "Explicit, backed-up v1 to v2 database migration")):
        _root(sub.add_parser(cmd, help=detail))

    def group(name: str, actions: dict[str, str]):
        parent = sub.add_parser(name)
        nested = parent.add_subparsers(dest="action", required=True)
        result = {}
        for action, description in actions.items():
            action_parser = nested.add_parser(action, help=description)
            _root(action_parser)
            result[action] = action_parser
        return result

    decisions = group("decision", {"add": "Propose a decision", "list": "List decisions", "update": "Edit a proposed decision", "approve": "Record explicit human approval", "reject": "Reject a proposal", "remove": "Soft-delete a decision"})
    decisions["add"].add_argument("--title", required=True)
    decisions["add"].add_argument("--rationale", default="")
    decisions["list"].add_argument("--all", action="store_true", help="Include removed records")
    for act in ("update", "approve", "reject", "remove"):
        decisions[act].add_argument("--id", required=True)
    decisions["update"].add_argument("--title")
    decisions["update"].add_argument("--rationale")
    decisions["approve"].add_argument("--by", required=True, help="Explicit approver identifier (user-asserted)")
    decisions["remove"].add_argument("--confirm", action="store_true")

    tasks = group("task", {"add": "Add a task", "list": "List tasks", "update": "Edit task title", "status": "Update unverified task status", "verify": "Verify with observed passing evidence", "remove": "Soft-delete a task"})
    tasks["add"].add_argument("--title", required=True)
    tasks["list"].add_argument("--all", action="store_true")
    for act in ("update", "status", "verify", "remove"):
        tasks[act].add_argument("--id", required=True)
    tasks["update"].add_argument("--title", required=True)
    tasks["status"].add_argument("--status", choices=TASK_STATUSES, required=True)
    tasks["verify"].add_argument("--evidence-id", required=True)
    tasks["remove"].add_argument("--confirm", action="store_true")

    evidence = group("evidence", {"record": "Record user-attested evidence (never sufficient to verify)",
                                  "run": "Explicitly execute a user-selected test, storing exit code only", "list": "List evidence metadata"})
    evidence["record"].add_argument("--task-id", required=True)
    evidence["record"].add_argument("--kind", choices=("test", "review", "manual"), required=True)
    evidence["record"].add_argument("--result", choices=("pass", "fail", "unknown"), required=True)
    evidence["record"].add_argument("--source-ref", required=True)
    evidence["run"].add_argument("--task-id", required=True)
    evidence["run"].add_argument("--timeout", type=int, default=120, help="1-600 seconds")
    evidence["run"].add_argument("command_args", nargs=argparse.REMAINDER)

    checkpoints = group("checkpoint", {"capture": "Capture actual Git SHA and dirty flags", "list": "List checkpoints"})
    return parser


def main(argv: list[str] | None = None) -> int:
    args = create_parser().parse_args(argv)
    supplied = args.root.expanduser().resolve()
    root = git_root(supplied)
    if args.command == "doctor":
        path = db_path(root) if root else None
        version, warning = None, None
        if path is not None and path.is_file() and not path.is_symlink() and not path.parent.is_symlink():
            try:
                version = schema_version(path)
            except (ValueError, OSError, sqlite3.DatabaseError) as exc:
                warning = f"Cannot inspect database: {type(exc).__name__}"
        report = {"tool_version": __version__, "python_supported": sys.version_info >= (3, 11),
                  "git_available": shutil.which("git") is not None, "git_repository": root is not None,
                  "initialized": version == SCHEMA_VERSION, "schema_version": version,
                  "migration_available": version == 1}
        if warning:
            report["warning"] = warning
        print(json.dumps(report, sort_keys=True, indent=2))
        return 0

    if root is None:
        print("Error: provide a directory inside a Git repository.", file=sys.stderr)
        return 2
    if args.command == "evidence" and args.action == "run" and not 1 <= args.timeout <= 600:
        print("Error: timeout must be between 1 and 600 seconds", file=sys.stderr)
        return 2
    try:
        if args.command == "init":
            _, created = init_state(root)
            result = {"message": "Initialized local project state" if created else "Project state already initialized",
                      "schema_version": SCHEMA_VERSION}
        elif args.command == "migrate":
            backup = migrate_state(root)
            result = {"schema_version": SCHEMA_VERSION,
                      "backup_created": backup.name, "message": "Migration completed; private v1 backup retained"}
        elif args.command == "decision":
            result = decision_action(root, args.action, args)
        elif args.command == "task":
            result = task_action(root, args.action, args)
        elif args.command == "evidence":
            result = evidence_action(root, args.action, args)
        elif args.command == "checkpoint":
            result = checkpoint_action(root, args.action)
        else:
            return 2
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (ValueError, OSError, sqlite3.DatabaseError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
