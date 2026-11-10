"""Validate the portable five SKILL.md documents without third-party packages."""
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1] / "skills"


class SkillTests(unittest.TestCase):
    def test_five_portable_skills(self):
        expected = {"research-first", "minimal-change", "systematic-debugging",
                    "verification-gates", "project-continuity-handoff"}
        self.assertEqual({p.name for p in ROOT.iterdir() if p.is_dir()}, expected)
        for folder in ROOT.iterdir():
            path = folder / "SKILL.md"
            self.assertTrue(path.is_file())
            text = path.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"))
            blocks = text.split("---\n", 2)
            self.assertEqual(len(blocks), 3)
            fields = {}
            for line in blocks[1].splitlines():
                key, sep, val = line.partition(":")
                self.assertEqual(sep, ":", line)
                fields[key] = val.strip()
            self.assertEqual(fields.get("name"), folder.name)
            self.assertRegex(folder.name, r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
            self.assertLessEqual(len(folder.name), 64)
            self.assertTrue(fields.get("description"))
            self.assertLessEqual(len(fields["description"]), 1024)
            self.assertEqual(fields.get("license"), "MIT")
            self.assertGreater(len(blocks[2].strip()), 150)

    def test_no_auto_deploy_permission_or_secret_collection(self):
        for doc in ROOT.glob("*/SKILL.md"):
            content = doc.read_text(encoding="utf-8").lower()
            self.assertNotIn("curl | bash", content)
            self.assertNotIn("ignore previous instructions", content)
            self.assertNotIn("always deploy automatically", content)


if __name__ == "__main__":
    unittest.main()
