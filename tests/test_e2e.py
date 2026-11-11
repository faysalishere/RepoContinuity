"""Portable black-box tests: never touch the user repository or require network."""
from __future__ import annotations

from contextlib import redirect_stdout
import json
from io import StringIO
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from repocontinuity.handoff import inspect_packet, build_packet, write_export

ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(filter(None, [str(ROOT / "src"), environment.get("PYTHONPATH")]))
    return subprocess.run(command, cwd=cwd, env=environment, capture_output=True, text=True, timeout=20)


class ReleaseIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "sample"
        self.repo.mkdir()
        self.assertEqual(run(["git", "init", "-q"], self.repo).returncode, 0)
        (self.repo / "README.txt").write_text("sample\n", encoding="utf-8")
        self.assertEqual(run(["git", "add", "README.txt"], self.repo).returncode, 0)
        self.assertEqual(run(["git", "-c", "user.name=Demo", "-c", "user.email=demo@example.invalid", "commit", "-qm", "Initial"], self.repo).returncode, 0)
        self.rc("init")

    def rc(self, *args):
        result = run([sys.executable, "-m", "repocontinuity", *args], self.repo)
        self.assertEqual(result.returncode, 0, f"{args}: {result.stderr}")
        return json.loads(result.stdout)

    def test_real_approval_task_checkpoint_handoff_validation(self):
        proposal = self.rc("decision", "add", "--title", "Keep current architecture")
        approved = self.rc("decision", "approve", "--id", proposal["id"], "--by", "Example owner")
        self.assertEqual(approved["status"], "approved")
        task = self.rc("task", "add", "--title", "Run regression tests")
        self.rc("task", "status", "--id", task["id"], "--status", "complete_unverified")
        self.rc("checkpoint", "capture")
        packet = self.rc("handoff", "export", "--format", "json")
        self.assertEqual(packet["tasks"][0]["status"], "complete_unverified")
        self.assertEqual(packet["checkpoints"][0]["status"], "unverified")
        self.assertEqual(packet["decisions"][0]["status"], "approved")
        file = Path(self.tmp.name) / "reviewed.json"
        file.write_text(json.dumps(packet), encoding="utf-8")
        outcome = self.rc("handoff", "import", "--file", str(file))
        self.assertTrue(outcome["valid_structure"])
        self.assertTrue(outcome["validation_only"])
        self.assertFalse(outcome["imported"])
        self.assertTrue(outcome["requires_review"])
        self.assertFalse(outcome["safe_to_apply_automatically"])

    def test_import_never_mutates_database(self):
        packet = self.rc("handoff", "export")
        file = Path(self.tmp.name) / "reviewed.json"
        file.write_text(json.dumps(packet), encoding="utf-8")
        db = self.repo / ".repocontinuity" / "state.sqlite3"
        before = db.read_bytes()
        self.rc("handoff", "validate", "--file", str(file))
        self.rc("handoff", "import", "--file", str(file))
        self.assertEqual(db.read_bytes(), before)

    def test_json_rejects_nan_and_infinity(self):
        packet = self.rc("handoff", "export")
        for constant in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(constant=constant):
                file = Path(self.tmp.name) / "evil.json"
                file.write_text(json.dumps(packet).replace('"dirty": false', f'"dirty": {constant}', 1), encoding="utf-8")
                result = run([sys.executable, "-m", "repocontinuity", "handoff", "validate", "--file", str(file)], self.repo)
                self.assertNotEqual(result.returncode, 0)

    def test_symlinked_output_ancestor_is_denied(self):
        external = Path(self.tmp.name) / "real-parent"
        external.mkdir()
        alias = Path(self.tmp.name) / "alias"
        try:
            alias.symlink_to(external, target_is_directory=True)
        except OSError:
            self.skipTest("Symlink permissions unavailable")
        with self.assertRaises(ValueError):
            write_export(alias / "handoff.json", "{}")
        self.assertEqual(list(external.iterdir()), [])

    def test_version_and_cli_help(self):
        version = run([sys.executable, "-m", "repocontinuity", "--version"], self.repo)
        self.assertIn("0.4.0b1", version.stdout)
        help_out = run([sys.executable, "-m", "repocontinuity", "handoff", "--help"], self.repo)
        self.assertIn("export", help_out.stdout)

    def test_disposable_demo_produces_unverified_not_false_claim(self):
        result = run([sys.executable, str(ROOT / "examples/quickstart_demo.py"), "--yes"], self.repo)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("UNVERIFIED", result.stdout)
        self.assertFalse((self.repo / "reviewed-handoff.json").exists())


if __name__ == "__main__":
    unittest.main()
