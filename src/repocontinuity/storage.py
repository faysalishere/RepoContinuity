"""Versioned local SQLite schema for the Phase 1 foundation.

No user activity is monitored. Future phases will add explicit read/write APIs.
"""

from __future__ import annotations

from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
import os
import sqlite3
import uuid

STATE_DIR = ".repocontinuity"
DB_FILENAME = "state.sqlite3"
SCHEMA_VERSION = 1

DDL = """
CREATE TABLE schema_meta (
    version INTEGER NOT NULL CHECK(version > 0)
);
CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE decisions (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    title TEXT NOT NULL,
    rationale TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL CHECK(status IN ('proposed', 'approved', 'rejected')),
    approved_by TEXT,
    approved_at TEXT,
    created_at TEXT NOT NULL,
    CHECK(status <> 'approved' OR (approved_by IS NOT NULL AND approved_at IS NOT NULL))
);
CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    title TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('planned','in_progress','blocked','complete_unverified','verified')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE evidence (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL REFERENCES tasks(id),
    kind TEXT NOT NULL CHECK(kind IN ('test','review','manual')),
    result TEXT NOT NULL CHECK(result IN ('pass','fail','unknown')),
    source_ref TEXT NOT NULL,
    recorded_at TEXT NOT NULL
);
CREATE TABLE checkpoints (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(id),
    commit_sha TEXT,
    status TEXT NOT NULL CHECK(status IN ('unverified','verified')),
    created_at TEXT NOT NULL
);
CREATE INDEX idx_tasks_project ON tasks(project_id);
CREATE INDEX idx_decisions_project ON decisions(project_id);
CREATE INDEX idx_evidence_task ON evidence(task_id);
CREATE INDEX idx_checkpoints_project ON checkpoints(project_id);
"""


def db_path(root: Path) -> Path:
    return root / STATE_DIR / DB_FILENAME


def schema_version(path: Path) -> int:
    # Open in read-only mode; a health check must never create a missing DB.
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=5)) as conn:
        row = conn.execute("SELECT version FROM schema_meta LIMIT 1").fetchone()
    if row is None:
        raise ValueError("Database is missing schema version")
    return int(row[0])


def init_state(root: Path) -> tuple[Path, bool]:
    state = root / STATE_DIR
    path = db_path(root)
    if state.is_symlink():
        raise ValueError("Refusing symlinked state directory")
    if state.exists() and not state.is_dir():
        raise ValueError("State path exists and is not a directory")
    if path.is_symlink():
        raise ValueError("Refusing symlinked database")
    if path.exists():
        found = schema_version(path)
        if found != SCHEMA_VERSION:
            raise ValueError(f"Unsupported schema version {found}; expected {SCHEMA_VERSION}")
        return path, False

    state.mkdir(mode=0o700, parents=False, exist_ok=True)
    if os.name == "posix":
        state.chmod(0o700)
    # Protect state even if users later git-add the hosting project recursively.
    ignore = state / ".gitignore"
    if not ignore.exists():
        ignore.write_text("*\n!.gitignore\n", encoding="utf-8")

    # SQLite creates the file; remove partially-created files if schema creation fails.
    try:
        with closing(sqlite3.connect(path, timeout=5)) as conn, conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.executescript(DDL)
            timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
            conn.execute("INSERT INTO schema_meta (version) VALUES (?)", (SCHEMA_VERSION,))
            conn.execute(
                "INSERT INTO projects (id, name, created_at) VALUES (?, ?, ?)",
                (str(uuid.uuid4()), root.name, timestamp),
            )
            conn.commit()
        if os.name == "posix":
            path.chmod(0o600)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return path, True
