from contextlib import redirect_stdout, redirect_stderr
from io import StringIO
from pathlib import Path
import json
import subprocess
import tempfile
import unittest

from repocontinuity.cli import main
from repocontinuity.storage import SCHEMA_VERSION


class CLITests(unittest.TestCase):
    def test_doctor_is_readonly_outside_git(self):
        with tempfile.TemporaryDirectory() as directory:
            out = StringIO()
            with redirect_stdout(out):
                result = main(["doctor", "--root", directory])
            self.assertEqual(result, 0)
            report = json.loads(out.getvalue())
            self.assertFalse(report["git_repository"])
            self.assertFalse(report["initialized"])
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_init_requires_git_repo(self):
        with tempfile.TemporaryDirectory() as directory:
            with redirect_stderr(StringIO()):
                result = main(["init", "--root", directory])
            self.assertEqual(result, 2)
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_git_repo_can_initialize_and_doctor(self):
        with tempfile.TemporaryDirectory() as directory:
            subprocess.run(["git", "init", "-q", directory], check=True)
            with redirect_stdout(StringIO()):
                self.assertEqual(main(["init", "--root", directory]), 0)
                self.assertEqual(main(["init", "--root", directory]), 0)
            out = StringIO()
            with redirect_stdout(out):
                self.assertEqual(main(["doctor", "--root", directory]), 0)
            report = json.loads(out.getvalue())
            self.assertTrue(report["git_repository"])
            self.assertTrue(report["initialized"])
            self.assertEqual(report["schema_version"], SCHEMA_VERSION)


if __name__ == "__main__":
    unittest.main()
