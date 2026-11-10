from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
import json
import sqlite3
import subprocess
import tempfile
import unittest

from repocontinuity.cli import main
from repocontinuity.storage import db_path, init_state


class FailClosedTests(unittest.TestCase):
    def test_unknown_schema_blocks_init_without_deleting_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", directory], check=True)
            path, _ = init_state(root)
            with sqlite3.connect(path) as db:
                db.execute("UPDATE schema_meta SET version = 999")
            with redirect_stderr(StringIO()) as errors:
                code = main(["init", "--root", directory])
            self.assertEqual(code, 1)
            self.assertIn("Unsupported schema version", errors.getvalue())
            self.assertTrue(path.exists())
            with sqlite3.connect(path) as db:
                self.assertEqual(db.execute("SELECT version FROM schema_meta").fetchone()[0], 999)

    def test_doctor_does_not_touch_source_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", directory], check=True)
            secret = root / ".env"
            secret.write_text("DUMMY_SECRET=placeholder-do-not-exfiltrate\n")
            with redirect_stdout(StringIO()) as output:
                self.assertEqual(main(["doctor", "--root", directory]), 0)
            self.assertNotIn("DUMMY_SECRET", output.getvalue())
            self.assertEqual(secret.read_text(), "DUMMY_SECRET=placeholder-do-not-exfiltrate\n")
            self.assertFalse(db_path(root).exists())

    def test_symlinked_database_fails_safely(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state = root / ".repocontinuity"
            state.mkdir()
            outside = root / "do-not-touch.txt"
            outside.write_text("unchanged")
            try:
                (state / "state.sqlite3").symlink_to(outside)
            except (OSError, NotImplementedError):
                self.skipTest("OS does not allow symlinks")
            with self.assertRaises(ValueError):
                init_state(root)
            self.assertEqual(outside.read_text(), "unchanged")


if __name__ == "__main__":
    unittest.main()
