"""Foundation schema tests; no user/project files are touched."""

from pathlib import Path
from contextlib import closing
import sqlite3
import tempfile
import unittest

from repocontinuity.storage import init_state, db_path, schema_version, SCHEMA_VERSION


class StorageTests(unittest.TestCase):
    def test_init_is_idempotent_and_versioned(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path, created = init_state(root)
            self.assertTrue(created)
            self.assertEqual(path, db_path(root))
            self.assertEqual(schema_version(path), SCHEMA_VERSION)
            with closing(sqlite3.connect(path)) as db:
                self.assertEqual(db.execute("SELECT COUNT(*) FROM projects").fetchone()[0], 1)
                self.assertEqual(db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0], 0)
                self.assertEqual(db.execute("PRAGMA foreign_key_list(evidence)").fetchone()[2], "tasks")
            _, created_again = init_state(root)
            self.assertFalse(created_again)
            with closing(sqlite3.connect(path)) as db:
                self.assertEqual(db.execute("SELECT COUNT(*) FROM projects").fetchone()[0], 1)
            self.assertIn("*", (root / ".repocontinuity" / ".gitignore").read_text())

    def test_init_rejects_symlinked_state_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root / "outside"
            outside.mkdir()
            try:
                (root / ".repocontinuity").symlink_to(outside, target_is_directory=True)
            except (NotImplementedError, OSError):
                self.skipTest("OS does not allow symlinks")
            with self.assertRaises(ValueError):
                init_state(root)
            self.assertFalse((outside / "state.sqlite3").exists())

    def test_readonly_schema_probe_cannot_create_database(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing.sqlite3"
            with self.assertRaises(sqlite3.OperationalError):
                schema_version(path)
            self.assertFalse(path.exists())

    def test_evidence_requires_real_task(self):
        with tempfile.TemporaryDirectory() as directory:
            path, _ = init_state(Path(directory))
            with closing(sqlite3.connect(path)) as db:
                db.execute("PRAGMA foreign_keys = ON")
                with self.assertRaises(sqlite3.IntegrityError):
                    db.execute("INSERT INTO evidence VALUES (?, ?, ?, ?, ?, ?)",
                               ("x", "no-task", "test", "pass", "test-log.txt", "2026-11-10T00:00:00Z"))


if __name__ == "__main__":
    unittest.main()
