"""Explicit local CRUD and evidence transitions; no automatic capture or sync."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sqlite3
import subprocess
import uuid

from .gitinfo import git_snapshot
from .storage import connection, log_action, project_id, utcnow

TASK_STATUSES = ("planned", "in_progress", "blocked", "complete_unverified")


def _required(value: str, label: str) -> str:
    if not value or not value.strip():
        raise ValueError(f"{label} must not be blank")
    if len(value) > 10000:
        raise ValueError(f"{label} is too long")
    return value.strip()


def _row(row: sqlite3.Row | None) -> dict:
    if row is None:
        raise ValueError("Record not found")
    return dict(row)


def _one(conn: sqlite3.Connection, table: str, item: str, *, include_deleted: bool = False) -> dict:
    if table not in ("decisions", "tasks", "evidence", "checkpoints"):
        raise ValueError("Unsupported table")
    condition = "" if include_deleted or table not in ("decisions", "tasks") else " AND deleted_at IS NULL"
    return _row(conn.execute(f"SELECT * FROM {table} WHERE id=?{condition}", (item,)).fetchone())


def _list(conn: sqlite3.Connection, table: str, *, all_items: bool = False) -> list[dict]:
    if table not in ("decisions", "tasks", "evidence", "checkpoints"):
        raise ValueError("Unsupported table")
    where = "" if all_items or table not in ("decisions", "tasks") else " WHERE deleted_at IS NULL"
    return [dict(r) for r in conn.execute(f"SELECT * FROM {table}{where} ORDER BY created_at, id")]


def decision_action(root: Path, action: str, args) -> object:
    if action == "list":
        with connection(root, readonly=True) as conn:
            return _list(conn, "decisions", all_items=args.all)
    with connection(root) as conn:
        with conn:
            project = project_id(conn)
            if action == "add":
                item = str(uuid.uuid4())
                now = utcnow()
                conn.execute("INSERT INTO decisions (id,project_id,title,rationale,status,created_at,updated_at) VALUES (?,?,?,?,'proposed',?,?)",
                             (item, project, _required(args.title, "title"), args.rationale or "", now, now))
                log_action(conn, project, "decision", item, "add")
            else:
                record = _one(conn, "decisions", args.id)
                item = record["id"]
                if action == "update":
                    if record["status"] != "proposed":
                        raise ValueError("Only proposed decisions can be edited")
                    title = _required(args.title, "title") if args.title is not None else record["title"]
                    rationale = args.rationale if args.rationale is not None else record["rationale"]
                    conn.execute("UPDATE decisions SET title=?,rationale=?,updated_at=? WHERE id=?",
                                 (title, rationale, utcnow(), item))
                elif action == "approve":
                    if record["status"] != "proposed":
                        raise ValueError("Only proposed decisions can be approved")
                    conn.execute("UPDATE decisions SET status='approved', approved_by=?,approved_at=?,updated_at=? WHERE id=?",
                                 (_required(args.by, "approver"), utcnow(), utcnow(), item))
                elif action == "reject":
                    if record["status"] != "proposed":
                        raise ValueError("Only proposed decisions can be rejected")
                    conn.execute("UPDATE decisions SET status='rejected',updated_at=? WHERE id=?", (utcnow(), item))
                elif action == "remove":
                    if not args.confirm:
                        raise ValueError("Removal requires --confirm; records are soft-deleted")
                    conn.execute("UPDATE decisions SET deleted_at=?,updated_at=? WHERE id=?", (utcnow(), utcnow(), item))
                else:
                    raise ValueError("Unsupported decision action")
                log_action(conn, project, "decision", item, action)
            return _one(conn, "decisions", item, include_deleted=True)


def task_action(root: Path, action: str, args) -> object:
    if action == "list":
        with connection(root, readonly=True) as conn:
            return _list(conn, "tasks", all_items=args.all)
    if action == "verify":
        state = git_snapshot(root)
        if state["worktree_dirty"]:
            raise ValueError("Cannot verify against a dirty working tree")
    with connection(root) as conn:
        with conn:
            project = project_id(conn)
            if action == "add":
                item = str(uuid.uuid4())
                now = utcnow()
                conn.execute("INSERT INTO tasks (id,project_id,title,status,created_at,updated_at) VALUES (?,?,?,'planned',?,?)",
                             (item, project, _required(args.title, "title"), now, now))
                log_action(conn, project, "task", item, "add")
            else:
                record = _one(conn, "tasks", args.id)
                item = record["id"]
                if action == "update":
                    if record["status"] == "verified":
                        raise ValueError("Reopen a verified task before editing")
                    conn.execute("UPDATE tasks SET title=?,updated_at=? WHERE id=?",
                                 (_required(args.title, "title"), utcnow(), item))
                elif action == "status":
                    if args.status not in TASK_STATUSES:
                        raise ValueError("Use task verify for verified status")
                    conn.execute("UPDATE tasks SET status=?,verified_evidence_id=NULL,updated_at=? WHERE id=?",
                                 (args.status, utcnow(), item))
                elif action == "verify":
                    evidence = _one(conn, "evidence", args.evidence_id)
                    if (evidence["task_id"] != item or evidence["kind"] != "test" or
                            evidence["result"] != "pass" or not evidence["observed"] or
                            evidence["git_dirty"] or evidence["git_sha"] != state["commit_sha"]):
                        raise ValueError("Passing observed test evidence for this task and clean commit required")
                    latest = git_snapshot(root)
                    if latest["worktree_dirty"] or latest["commit_sha"] != state["commit_sha"]:
                        raise ValueError("Git state changed during verification")
                    conn.execute("UPDATE tasks SET status='verified',verified_evidence_id=?,updated_at=? WHERE id=?",
                                 (args.evidence_id, utcnow(), item))
                elif action == "remove":
                    if not args.confirm:
                        raise ValueError("Removal requires --confirm; records are soft-deleted")
                    conn.execute("UPDATE tasks SET deleted_at=?,updated_at=? WHERE id=?", (utcnow(), utcnow(), item))
                else:
                    raise ValueError("Unsupported task action")
                log_action(conn, project, "task", item, action)
            return _one(conn, "tasks", item, include_deleted=True)


def evidence_action(root: Path, action: str, args) -> object:
    if action == "list":
        with connection(root, readonly=True) as conn:
            return _list(conn, "evidence")
    observed = 0
    sha = None
    dirty = 1
    if action == "record":
        kind = args.kind
        result = args.result
        source = _required(args.source_ref, "source_ref")
        if kind not in ("test", "review", "manual") or result not in ("pass", "fail", "unknown"):
            raise ValueError("Invalid evidence kind or result")
    elif action == "run":
        # Reject nonexistent/archived task IDs before executing ANY user command.
        with connection(root, readonly=True) as existing:
            _one(existing, "tasks", args.task_id)
        command = args.command_args
        if command and command[0] == "--":
            command = command[1:]
        if not command:
            raise ValueError("Provide an explicit command after --")
        # Never store raw argv or stdout/stderr: they may contain secrets.
        source = "observed-command:sha256:" + hashlib.sha256(json.dumps(command).encode("utf-8")).hexdigest()
        before = git_snapshot(root)
        try:
            run = subprocess.run(command, cwd=root, stdin=subprocess.DEVNULL,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                 check=False, timeout=args.timeout)
            result = "pass" if run.returncode == 0 else "fail"
        except (OSError, subprocess.TimeoutExpired):
            result = "fail"
        after = git_snapshot(root)
        sha = before["commit_sha"]
        dirty = int(before["worktree_dirty"] or after["worktree_dirty"] or before["commit_sha"] != after["commit_sha"])
        observed = 1
        kind = "test"
    else:
        raise ValueError("Unsupported evidence action")
    with connection(root) as conn, conn:
        _one(conn, "tasks", args.task_id)
        item = str(uuid.uuid4())
        conn.execute("INSERT INTO evidence (id,task_id,kind,result,source_ref,recorded_at,observed,git_sha,git_dirty) VALUES (?,?,?,?,?,?,?,?,?)",
                     (item, args.task_id, kind, result, source, utcnow(), observed, sha, dirty))
        log_action(conn, project_id(conn), "evidence", item, action)
        return _one(conn, "evidence", item)


def checkpoint_action(root: Path, action: str) -> object:
    if action == "list":
        with connection(root, readonly=True) as conn:
            return _list(conn, "checkpoints")
    if action != "capture":
        raise ValueError("Unsupported checkpoint action")
    state = git_snapshot(root)
    with connection(root) as conn, conn:
        item = str(uuid.uuid4())
        project = project_id(conn)
        conn.execute("INSERT INTO checkpoints (id,project_id,commit_sha,status,created_at,worktree_dirty,staged_dirty,branch) VALUES (?,?,?,'unverified',?,?,?,?)",
                     (item, project, state["commit_sha"], utcnow(), int(state["worktree_dirty"]), int(state["staged_dirty"]), state["branch"]))
        log_action(conn, project, "checkpoint", item, "capture")
        return _one(conn, "checkpoints", item)
