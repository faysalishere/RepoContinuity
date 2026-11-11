"""Offline study aggregation tests. Internal/synthetic input must never count as users."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from scripts.summarize_study import read_reports, summarize


def entry(identifier: str, **overrides) -> dict:
    row = {
        "study_id": identifier, "origin": "external", "consent": True, "os": "Linux",
        "setup_success": True, "setup_minutes": 4.5, "handoff_answers_correct": 4,
        "handoff_mode": "ai", "false_verified_claim": False, "would_use_again": None,
        "repeat_after_7_days": None,
    }
    row.update(overrides)
    return row


class StudyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "reports.jsonl"

    def write(self, records):
        self.path.write_text("\n".join(json.dumps(r) for r in records) + "\n", encoding="utf-8")
        return read_reports(self.path)

    def test_zero_data_cannot_claim_users(self):
        self.assertEqual(summarize(read_reports(None))["status"], "NO_EXTERNAL_EVIDENCE")
        self.assertEqual(summarize(read_reports(None))["independent_testers"], 0)

    def test_internal_runs_do_not_count(self):
        result = summarize(self.write([entry("automated_1", origin="internal")]))
        self.assertEqual(result["status"], "NO_EXTERNAL_EVIDENCE")
        self.assertEqual(result["internal_runs_excluded"], 1)

    def test_real_study_thresholds_are_manual_gate_only(self):
        participants = [entry(f"participant_{i}", os="Linux" if i % 2 else "Windows",
                              repeat_after_7_days=True if i < 3 else None) for i in range(8)]
        result = summarize(self.write(participants))
        self.assertEqual(result["independent_testers"], 8)
        self.assertEqual(result["handoff_answers"], {"correct": 32, "possible": 40})
        self.assertEqual(result["status"], "READY_FOR_MANUAL_REVIEW")
        self.assertTrue(all(result["acceptance_checks"].values()))

    def test_false_verified_flag_blocks_review(self):
        result = summarize(self.write([entry("report1", false_verified_claim=True)]))
        self.assertEqual(result["status"], "INVESTIGATE_SAFETY")
        self.assertEqual(result["reported_false_verified_claims"], 1)

    def test_duplicate_respondent_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "Duplicate respondent"):
            self.write([entry("same"), entry("same")])

    def test_extra_field_and_missing_consent_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing or unexpected"):
            self.write([entry("extra", private="should not be ingested")])
        with self.assertRaisesRegex(ValueError, "consent"):
            self.write([entry("no-consent", consent=False)])

    def test_invalid_nan_and_duplicate_json_keys_rejected(self):
        payload = json.dumps(entry("nan")).replace('"setup_minutes": 4.5', '"setup_minutes": NaN')
        self.path.write_text(payload, encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "invalid JSON"):
            read_reports(self.path)
        payload = json.dumps(entry("dup")).replace('"origin": "external"', '"origin": "external", "origin": "internal"')
        self.path.write_text(payload, encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "invalid JSON"):
            read_reports(self.path)

    def test_symlink_refused_and_input_bounded(self):
        destination = Path(self.temp.name) / "data.txt"
        destination.write_text("", encoding="utf-8")
        try:
            self.path.symlink_to(destination)
        except OSError:
            self.skipTest("Symlinks unavailable")
        with self.assertRaisesRegex(ValueError, "non-symlink"):
            read_reports(self.path)

    def test_report_does_not_reveal_identifiers(self):
        report = summarize(self.write([entry("privatepseudonym")]))
        self.assertNotIn("privatepseudonym", json.dumps(report))
        self.assertEqual(report["handoff_modes"]["ai"], 1)


if __name__ == "__main__":
    unittest.main()
