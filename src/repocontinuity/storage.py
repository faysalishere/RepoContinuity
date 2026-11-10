"""SQLite persistence with explicit, backed-up migration from schema v1 to v2.

Connections are always closed for Windows compatibility. Only explicit commands write.
"""
from __future__ import annotations

from contextlib import closing, contextmanager
from datetime import datetime, timezone
from pathlib import Path
import os
import sqlite3
import uuid

STATE_DIR = ".repocontinuity"
DB_FILENAME = "state.sqlite3"
SCHEMA_VERSION = 2

DDL = """
CREATE TABLE schema_meta (version INTEGER NOT NULL CHECK(version > 0));
CREATE TABLE projects (id TEXT PRIMARY KEY, name TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE decisions (
    id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id),
    title TEXT NOT NULL, rationale TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL CHECK(status IN ('proposed','approved','rejected')),
    approved_by TEXT, approved_at TEXT, created_at TEXT NOT NULL,
    updated_at TEXT, deleted_at TEXT,
    CHECK(status <> 'approved' OR (approved_by IS NOT NULL AND approved_at IS NOT NULL))
);
CREATE TABLE tasks (
    id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id),
    title TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('planned','in_progress','blocked','complete_unverified','verified')),
    created_at TEXT NOT NULL, updated_at TEXT NOT NULL, deleted_at TEXT,
    verified_evidence_id TEXT REFERENCES evidence(id)
);
CREATE TABLE evidence (
    id TEXT PRIMARY KEY, task_id TEXT NOT NULL REFERENCES tasks(id),
    kind TEXT NOT NULL CHECK(kind IN ('test','review','manual')),
    result TEXT NOT NULL CHECK(result IN ('pass','fail','unknown')),
    source_ref TEXT NOT NULL, recorded_at TEXT NOT NULL,
    observed INTEGER NOT NULL DEFAULT 0 CHECK(observed IN (0,1)),
    git_sha TEXT, git_dirty INTEGER NOT NULL DEFAULT 1 CHECK(git_dirty IN (0,1))
);
CREATE TABLE checkpoints (
    id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id),
    commit_sha TEXT, status TEXT NOT NULL CHECK(status IN ('unverified','verified')),
    created_at TEXT NOT NULL,
    worktree_dirty INTEGER NOT NULL DEFAULT 1 CHECK(worktree_dirty IN (0,1)),
    staged_dirty INTEGER NOT NULL DEFAULT 1 CHECK(staged_dirty IN (0,1)),
    branch TEXT
);
CREATE TABLE activity_log (
    id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id),
    entity_type TEXT NOT NULL, entity_id TEXT NOT NULL, action TEXT NOT NULL,
    recorded_at TEXT NOT NULL
);
CREATE INDEX idx_tasks_project ON tasks(project_id);
CREATE INDEX idx_decisions_project ON decisions(project_id);
CREATE INDEX idx_evidence_task ON evidence(task_id);
CREATE INDEX idx_checkpoints_project ON checkpoints(project_id);
CREATE INDEX idx_activity_project ON activity_log(project_id);
"""

# A database owner can still edit SQLite directly: this guard prevents accidental
# false verification from raw UPDATEs, not deliberate tampering.
VERIFY_TRIGGER = """
CREATE TRIGGER verify_task_guard BEFORE UPDATE OF status, verified_evidence_id ON tasks
WHEN NEW.status = 'verified'
BEGIN
  SELECT CASE WHEN NEW.verified_evidence_id IS NULL OR NOT EXISTS (
    SELECT 1 FROM evidence e WHERE e.id = NEW.verified_evidence_id
    AND e.task_id = NEW.id AND e.kind = 'test' AND e.result = 'pass'
    AND e.observed = 1 AND e.git_dirty = 0 AND e.git_sha IS NOT NULL
  ) THEN RAISE(ABORT, 'verified task requires observed passing test evidence') END;
END;
"""

TASK_INSERT_TRIGGER = """
CREATE TRIGGER task_verified_insert_guard BEFORE INSERT ON tasks
WHEN NEW.status = 'verified'
BEGIN SELECT RAISE(ABORT, 'verified task requires observed evidence via task verify'); END;
"""

EVIDENCE_UPDATE_TRIGGER = """
CREATE TRIGGER evidence_immutable_update BEFORE UPDATE ON evidence
BEGIN SELECT RAISE(ABORT, 'evidence is immutable'); END;
"""
EVIDENCE_DELETE_TRIGGER = """
CREATE TRIGGER evidence_immutable_delete BEFORE DELETE ON evidence
BEGIN SELECT RAISE(ABORT, 'evidence is immutable'); END;
"""
CHECKPOINT_UPDATE_TRIGGER = """
CREATE TRIGGER checkpoint_unverified_update BEFORE UPDATE OF status ON checkpoints
WHEN NEW.status = 'verified'
BEGIN SELECT RAISE(ABORT, 'checkpoint verification is not implemented'); END;
"""
CHECKPOINT_INSERT_TRIGGER = """
CREATE TRIGGER checkpoint_unverified_insert BEFORE INSERT ON checkpoints
WHEN NEW.status = 'verified'
BEGIN SELECT RAISE(ABORT, 'checkpoint verification is not implemented'); END;
"""
TRIGGERS_V2 = (VERIFY_TRIGGER, TASK_INSERT_TRIGGER, EVIDENCE_UPDATE_TRIGGER, EVIDENCE_DELETE_TRIGGER,
               CHECKPOINT_UPDATE_TRIGGER, CHECKPOINT_INSERT_TRIGGER)

MIGRATION_V1_TO_V2 = [
    "ALTER TABLE decisions ADD COLUMN updated_at TEXT",
    "ALTER TABLE decisions ADD COLUMN deleted_at TEXT",
    "ALTER TABLE tasks ADD COLUMN deleted_at TEXT",
    "ALTER TABLE tasks ADD COLUMN verified_evidence_id TEXT REFERENCES evidence(id)",
    "ALTER TABLE evidence ADD COLUMN observed INTEGER NOT NULL DEFAULT 0 CHECK(observed IN (0,1))",
    "ALTER TABLE evidence ADD COLUMN git_sha TEXT",
    "ALTER TABLE evidence ADD COLUMN git_dirty INTEGER NOT NULL DEFAULT 1 CHECK(git_dirty IN (0,1))",
    "ALTER TABLE checkpoints ADD COLUMN worktree_dirty INTEGER NOT NULL DEFAULT 1 CHECK(worktree_dirty IN (0,1))",
    "ALTER TABLE checkpoints ADD COLUMN staged_dirty INTEGER NOT NULL DEFAULT 1 CHECK(staged_dirty IN (0,1))",
    "ALTER TABLE checkpoints ADD COLUMN branch TEXT",
    "CREATE TABLE activity_log (id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id), entity_type TEXT NOT NULL, entity_id TEXT NOT NULL, action TEXT NOT NULL, recorded_at TEXT NOT NULL)",
    "CREATE INDEX idx_activity_project ON activity_log(project_id)",
    # Preserve legacy rows, but do not claim their unobserved results are verified.
    "UPDATE tasks SET status = 'complete_unverified' WHERE status = 'verified'",
    "UPDATE checkpoints SET status = 'unverified' WHERE status = 'verified'",
    *TRIGGERS_V2,
    "UPDATE schema_meta SET version = 2 WHERE version = 1",
]


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def db_path(root: Path) -> Path:
    return root / STATE_DIR / DB_FILENAME


def _validate_paths(root: Path) -> Path:
    state = root / STATE_DIR
    path = db_path(root)
    if state.is_symlink() or (state.exists() and not state.is_dir()):
        raise ValueError("Refusing symlinked or invalid state directory")
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise ValueError("Refusing symlinked or invalid database file")
    return path


@contextmanager
def connection(root: Path, *, readonly: bool = False):
    path = _validate_paths(root)
    if not path.is_file():
        raise ValueError("Project is not initialized; run init")
    uri = path.as_uri() + "?mode=ro" if readonly else str(path)
    with closing(sqlite3.connect(uri, uri=readonly, timeout=5)) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        version = conn.execute("SELECT version FROM schema_meta LIMIT 1").fetchone()
        if version is None or int(version[0]) != SCHEMA_VERSION:
            raise ValueError("Unsupported schema version; run migrate if database is v1")
        yield conn


def schema_version(path: Path) -> int:
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=5)) as conn:
        row = conn.execute("SELECT version FROM schema_meta LIMIT 1").fetchone()
    if row is None:
        raise ValueError("Database is missing schema version")
    return int(row[0])


def init_state(root: Path) -> tuple[Path, bool]:
    state = root / STATE_DIR
    path = _validate_paths(root)
    if path.exists():
        found = schema_version(path)
        if found != SCHEMA_VERSION:
            raise ValueError(f"Unsupported schema version {found}; run migrate (expected {SCHEMA_VERSION})")
        return path, False

    state.mkdir(mode=0o700, parents=False, exist_ok=True)
    if os.name == "posix":
        state.chmod(0o700)
    ignore = state / ".gitignore"
    if not ignore.exists():
        ignore.write_text("*\n", encoding="utf-8")

    try:
        with closing(sqlite3.connect(path, timeout=5)) as conn, conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.executescript(DDL)
            for trigger in TRIGGERS_V2:
                conn.execute(trigger)
            conn.execute("INSERT INTO schema_meta (version) VALUES (?)", (SCHEMA_VERSION,))
            conn.execute(
                "INSERT INTO projects (id, name, created_at) VALUES (?, ?, ?)",
                (str(uuid.uuid4()), root.name, utcnow()),
            )
            conn.commit()
        if os.name == "posix":
            path.chmod(0o600)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    return path, True


def migrate_state(root: Path) -> Path:
    """Explicit non-destructive v1->v2; first take SQLite-consistent .v1.bak snapshot."""
    path = _validate_paths(root)
    if not path.is_file():
        raise ValueError("Project is not initialized")
    found = schema_version(path)
    if found == SCHEMA_VERSION:
        raise ValueError("Already on schema version 2; no migration needed")
    if found != 1:
        raise ValueError(f"Unsupported schema version {found}; no migration attempted")
    backup = path.with_suffix(path.suffix + ".v1.bak")
    if backup.exists() or backup.is_symlink():
        raise ValueError("Migration backup path already exists; preserve it and investigate")
    with closing(sqlite3.connect(path, timeout=5)) as source:
        with closing(sqlite3.connect(backup, timeout=5)) as destination:
            source.backup(destination)
    if os.name == "posix":
        backup.chmod(0o600)
    try:
        with closing(sqlite3.connect(path, timeout=5)) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("BEGIN IMMEDIATE")
            if int(conn.execute("SELECT version FROM schema_meta").fetchone()[0]) != 1:
                raise ValueError("Schema changed during backup; aborting")
            for statement in MIGRATION_V1_TO_V2:
                conn.execute(statement)
            conn.commit()
    except Exception:
        # Keep backup and original for manual inspection; never drop user data.
        raise
    return backup


def project_id(conn: sqlite3.Connection) -> str:
    row = conn.execute("SELECT id FROM projects ORDER BY created_at LIMIT 1").fetchone()
    if row is None:
        raise ValueError("Database does not contain an initialized project")
    return row[0]


def log_action(conn: sqlite3.Connection, project: str, entity_type: str, entity_id: str, action: str):
    conn.execute(
        "INSERT INTO activity_log VALUES (?,?,?,?,?,?)",
        (str(uuid.uuid4()), project, entity_type, entity_id, action, utcnow()),
    )
