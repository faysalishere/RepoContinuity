"""Phase 2 integration tests: explicit approvals, evidence, migration, Git states."""
from __future__ import annotations

from contextlib import redirect_stdout, redirect_stderr, closing
from io import StringIO
from pathlib import Path
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from repocontinuity.cli import main
from repocontinuity.gitinfo import git_snapshot
from repocontinuity.storage import db_path, init_state, migrate_state, schema_version, SCHEMA_VERSION


def invoke(*parts):
    out, err = StringIO(), StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(list(parts))
    return code, json.loads(out.getvalue()) if out.getvalue().strip() else None, err.getvalue()


def git(root, *args):
    subprocess.run(["git", "-C", str(root), *args], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


class Phase2Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        git(self.root, "init", "-q")
        git(self.root, "-c", "user.name=Local Test", "-c", "user.email=test@example.invalid", "commit", "-q", "--allow-empty", "-m", "base")
        code, response, error = invoke("init", "--root", str(self.root))
        self.assertEqual(code, 0, error)
        self.assertEqual(response["schema_version"], 2)

    def call(self, *args):
        return invoke(args[0], args[1], "--root", str(self.root), *args[2:]) if len(args) >= 2 else invoke(*args, "--root", str(self.root))

    def test_init_state_does_not_mark_repository_dirty(self):
        state = git_snapshot(self.root)
        self.assertFalse(state["worktree_dirty"])
        self.assertEqual(len(state["commit_sha"]), 40)
        self.assertFalse(state["staged_dirty"])

    def test_approval_must_be_explicit_and_is_immutable(self):
        code, proposed, err = self.call("decision", "add", "--title", "Keep existing DB", "--rationale", "No rewrite")
        self.assertEqual(code, 0, err)
        self.assertEqual(proposed["status"], "proposed")
        code, _, _ = self.call("decision", "approve", "--id", proposed["id"], "--by", " ")
        self.assertEqual(code, 1)
        code, approved, err = self.call("decision", "approve", "--id", proposed["id"], "--by", "Owner")
        self.assertEqual(code, 0, err)
        self.assertEqual(approved["approved_by"], "Owner")
        self.assertIsNotNone(approved["approved_at"])
        code, _, _ = self.call("decision", "update", "--id", proposed["id"], "--title", "Rewrite everything")
        self.assertEqual(code, 1)
        code, listed, _ = self.call("decision", "list")
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0]["title"], "Keep existing DB")

    def test_decision_and_task_soft_delete(self):
        _, proposed, _ = self.call("decision", "add", "--title", "Candidate")
        code, _, _ = self.call("decision", "remove", "--id", proposed["id"])
        self.assertEqual(code, 1)
        code, removed, _ = self.call("decision", "remove", "--id", proposed["id"], "--confirm")
        self.assertEqual(code, 0)
        self.assertTrue(removed["deleted_at"])
        self.assertEqual(self.call("decision", "list")[1], [])
        self.assertEqual(len(self.call("decision", "list", "--all")[1]), 1)
        _, task, _ = self.call("task", "add", "--title", "Implement")
        code, removed, _ = self.call("task", "remove", "--id", task["id"], "--confirm")
        self.assertEqual(code, 0)
        self.assertTrue(removed["deleted_at"])
        self.assertEqual(self.call("task", "list")[1], [])

    def test_checkpoint_clean_and_dirty(self):
        _, clean, err = self.call("checkpoint", "capture")
        self.assertFalse(clean["worktree_dirty"], err)
        self.assertEqual(clean["status"], "unverified")
        self.assertEqual(clean["commit_sha"], git_snapshot(self.root)["commit_sha"])
        (self.root / "newfile.txt").write_text("changes\n")
        _, dirty, err = self.call("checkpoint", "capture")
        self.assertTrue(dirty["worktree_dirty"], err)
        self.assertFalse(dirty["staged_dirty"])
        git(self.root, "add", "newfile.txt")
        _, staged, _ = self.call("checkpoint", "capture")
        self.assertTrue(staged["staged_dirty"])
        self.assertEqual(len(self.call("checkpoint", "list")[1]), 3)

    def test_self_attested_pass_cannot_verify(self):
        _, task, _ = self.call("task", "add", "--title", "Test target")
        _, evidence, err = self.call("evidence", "record", "--task-id", task["id"], "--kind", "test", "--result", "pass", "--source-ref", "report.txt")
        self.assertEqual(evidence["observed"], 0, err)
        code, _, _ = self.call("task", "verify", "--id", task["id"], "--evidence-id", evidence["id"])
        self.assertEqual(code, 1)
        with closing(sqlite3.connect(db_path(self.root))) as conn:
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("UPDATE tasks SET status='verified',verified_evidence_id=? WHERE id=?", (evidence["id"], task["id"]))

    def test_observed_pass_can_verify_and_reopen(self):
        _, task, _ = self.call("task", "add", "--title", "Check")
        code, evidence, err = self.call("evidence", "run", "--task-id", task["id"], "--", sys.executable, "-c", "pass")
        self.assertEqual(code, 0, err)
        self.assertEqual(evidence["result"], "pass")
        self.assertEqual(evidence["observed"], 1)
        self.assertFalse(evidence["git_dirty"])
        self.assertTrue(evidence["source_ref"].startswith("observed-command:sha256:"))
        code, verified, err = self.call("task", "verify", "--id", task["id"], "--evidence-id", evidence["id"])
        self.assertEqual(code, 0, err)
        self.assertEqual(verified["status"], "verified")
        self.assertEqual(verified["verified_evidence_id"], evidence["id"])
        code, _, _ = self.call("task", "update", "--id", task["id"], "--title", "Alter")
        self.assertEqual(code, 1)
        code, reopened, err = self.call("task", "status", "--id", task["id"], "--status", "in_progress")
        self.assertEqual(code, 0, err)
        self.assertIsNone(reopened["verified_evidence_id"])
        code, changed, _ = self.call("task", "update", "--id", task["id"], "--title", "Alter")
        self.assertEqual(code, 0)
        self.assertEqual(changed["title"], "Alter")

    def test_observed_failure_and_stale_commit_block_verification(self):
        _, task, _ = self.call("task", "add", "--title", "Regression")
        _, failed, _ = self.call("evidence", "run", "--task-id", task["id"], "--", sys.executable, "-c", "raise SystemExit(1)")
        self.assertEqual(failed["result"], "fail")
        self.assertEqual(self.call("task", "verify", "--id", task["id"], "--evidence-id", failed["id"])[0], 1)
        _, passed, _ = self.call("evidence", "run", "--task-id", task["id"], "--", sys.executable, "-c", "pass")
        git(self.root, "-c", "user.name=Local Test", "-c", "user.email=test@example.invalid", "commit", "-q", "--allow-empty", "-m", "next")
        self.assertEqual(self.call("task", "verify", "--id", task["id"], "--evidence-id", passed["id"])[0], 1)

    def test_dirty_run_is_not_sufficient(self):
        _, task, _ = self.call("task", "add", "--title", "Writes")
        cmd = [sys.executable, "-c", "from pathlib import Path; Path('test-generated.txt').write_text('x')"]
        code, recorded, err = self.call("evidence", "run", "--task-id", task["id"], "--", *cmd)
        self.assertEqual(code, 0, err)
        self.assertEqual(recorded["result"], "pass")
        self.assertEqual(recorded["git_dirty"], 1)
        self.assertEqual(self.call("task", "verify", "--id", task["id"], "--evidence-id", recorded["id"])[0], 1)

    def test_failed_validation_does_not_execute_nonexistent_task(self):
        output = self.root / "should-not-be-created.txt"
        code, _, err = self.call("evidence", "run", "--task-id", "missing-task", "--",
                                 sys.executable, "-c", f"from pathlib import Path; Path({str(output)!r}).write_text('BAD')")
        self.assertEqual(code, 1)
        self.assertFalse(output.exists())
        self.assertIn("not found", err.lower())

    def test_verified_flags_cannot_be_faked_in_sql(self):
        _, task, _ = self.call("task", "add", "--title", "Test")
        _, captured, _ = self.call("checkpoint", "capture")
        with closing(sqlite3.connect(db_path(self.root))) as conn:
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("UPDATE tasks SET status='verified' WHERE id=?", (task["id"],))
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("INSERT INTO tasks (id,project_id,title,status,created_at,updated_at) VALUES ('fake','unreal','fake','verified','now','now')")
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("UPDATE checkpoints SET status='verified' WHERE id=?", (captured["id"],))
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("INSERT INTO checkpoints (id,project_id,status,created_at) VALUES ('fake','x','verified','today')")

    def test_observed_evidence_rows_are_append_only(self):
        _, task, _ = self.call("task", "add", "--title", "Immutable")
        _, recorded, _ = self.call("evidence", "record", "--task-id", task["id"],
                                   "--kind", "test", "--result", "fail", "--source-ref", "log-file")
        with closing(sqlite3.connect(db_path(self.root))) as conn:
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("UPDATE evidence SET result='pass' WHERE id=?", (recorded["id"],))
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("DELETE FROM evidence WHERE id=?", (recorded["id"],))

    def test_dirty_tree_after_passing_test_blocks_verification(self):
        _, task, _ = self.call("task", "add", "--title", "Check")
        _, passed, _ = self.call("evidence", "run", "--task-id", task["id"], "--", sys.executable, "-c", "pass")
        (self.root / "uncommitted.py").write_text("print('changed')\n")
        code, _, err = self.call("task", "verify", "--id", task["id"], "--evidence-id", passed["id"])
        self.assertEqual(code, 1)
        self.assertIn("dirty", err.lower())

    def test_audit_log_tracks_mutations(self):
        _, decision, _ = self.call("decision", "add", "--title", "Audit")
        self.call("decision", "approve", "--id", decision["id"], "--by", "Owner")
        with closing(sqlite3.connect(db_path(self.root))) as conn:
            entries = conn.execute("SELECT action FROM activity_log ORDER BY rowid").fetchall()
        self.assertEqual([x[0] for x in entries], ["add", "approve"])

    def test_schema_v1_migration_preserves_records_and_creates_backup(self):
        # Rebuild a real v1 layout from the published Phase 1 tables.
        path = db_path(self.root)
        path.unlink()
        with closing(sqlite3.connect(path)) as conn:
            conn.executescript("""
                CREATE TABLE schema_meta (version INTEGER NOT NULL CHECK(version>0));
                CREATE TABLE projects (id TEXT PRIMARY KEY,name TEXT NOT NULL,created_at TEXT NOT NULL);
                CREATE TABLE decisions (id TEXT PRIMARY KEY, project_id TEXT NOT NULL REFERENCES projects(id),title TEXT NOT NULL,rationale TEXT NOT NULL DEFAULT '',status TEXT NOT NULL CHECK(status IN ('proposed','approved','rejected')),approved_by TEXT,approved_at TEXT,created_at TEXT NOT NULL,CHECK(status <> 'approved' OR (approved_by IS NOT NULL AND approved_at IS NOT NULL)));
                CREATE TABLE tasks (id TEXT PRIMARY KEY,project_id TEXT NOT NULL REFERENCES projects(id),title TEXT NOT NULL,status TEXT NOT NULL CHECK(status IN ('planned','in_progress','blocked','complete_unverified','verified')),created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
                CREATE TABLE evidence (id TEXT PRIMARY KEY,task_id TEXT NOT NULL REFERENCES tasks(id),kind TEXT NOT NULL CHECK(kind IN ('test','review','manual')),result TEXT NOT NULL CHECK(result IN ('pass','fail','unknown')),source_ref TEXT NOT NULL,recorded_at TEXT NOT NULL);
                CREATE TABLE checkpoints (id TEXT PRIMARY KEY,project_id TEXT NOT NULL REFERENCES projects(id),commit_sha TEXT,status TEXT NOT NULL CHECK(status IN ('unverified','verified')),created_at TEXT NOT NULL);
                CREATE INDEX idx_tasks_project ON tasks(project_id);
                CREATE INDEX idx_decisions_project ON decisions(project_id);
                CREATE INDEX idx_evidence_task ON evidence(task_id);
                CREATE INDEX idx_checkpoints_project ON checkpoints(project_id);
                INSERT INTO schema_meta VALUES (1);
                INSERT INTO projects VALUES ('keep-me','Original Project','2026-01-01');
                INSERT INTO decisions VALUES ('decision-v1','keep-me','Keep database','reason','approved','Owner','2026-01-02','2026-01-01');
                INSERT INTO tasks VALUES ('task-v1','keep-me','Do not lose','verified','2026-01-01','2026-01-01');
                INSERT INTO checkpoints VALUES ('checkpoint-v1','keep-me','0123456789012345678901234567890123456789','verified','2026-01-01');
            """)
        self.assertEqual(self.call("init")[0], 1)
        _, pre, _ = invoke("doctor", "--root", str(self.root))
        self.assertEqual(pre["schema_version"], 1)
        self.assertTrue(pre["migration_available"])
        code, result, error = self.call("migrate")
        self.assertEqual(code, 0, error)
        self.assertEqual(result["schema_version"], SCHEMA_VERSION)
        self.assertEqual(schema_version(path), SCHEMA_VERSION)
        self.assertTrue(path.with_suffix(".sqlite3.v1.bak").exists())
        with closing(sqlite3.connect(path)) as conn:
            self.assertEqual(conn.execute("SELECT title FROM tasks WHERE id='task-v1'").fetchone()[0], "Do not lose")
            self.assertEqual(conn.execute("SELECT status FROM tasks WHERE id='task-v1'").fetchone()[0], "complete_unverified")
            self.assertEqual(conn.execute("SELECT status FROM checkpoints WHERE id='checkpoint-v1'").fetchone()[0], "unverified")
            self.assertEqual(conn.execute("SELECT status FROM decisions WHERE id='decision-v1'").fetchone()[0], "approved")
        with closing(sqlite3.connect(path.with_suffix(".sqlite3.v1.bak"))) as conn:
            self.assertEqual(conn.execute("SELECT version FROM schema_meta").fetchone()[0], 1)
            self.assertEqual(conn.execute("SELECT status FROM tasks WHERE id='task-v1'").fetchone()[0], "verified")
        self.assertEqual(self.call("migrate")[0], 1)


if __name__ == "__main__":
    unittest.main()
