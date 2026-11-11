"""Offline, consent-gated aggregate of explicitly supplied pilot observations.

No network access, no telemetry, no issue scraping. Synthetic/internal observations
are excluded from real-user metrics and no respondent identifiers are printed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import statistics
import sys

MAX_BYTES = 256 * 1024
MAX_ROWS = 200
FIELDS = {
    "study_id", "origin", "consent", "os", "setup_success", "setup_minutes",
    "handoff_answers_correct", "handoff_mode", "false_verified_claim", "would_use_again",
    "repeat_after_7_days",
}
VALID_OS = {"Windows", "macOS", "Linux", "Other"}


def _validate(row: object, index: int) -> dict:
    if type(row) is not dict or set(row) != FIELDS:
        raise ValueError(f"Line {index}: missing or unexpected fields")
    if type(row["study_id"]) is not str or not re.fullmatch(r"[A-Za-z0-9_-]{1,40}", row["study_id"]):
        raise ValueError(f"Line {index}: invalid pseudonymous study_id")
    if type(row["origin"]) is not str or row["origin"] not in ("external", "internal"):
        raise ValueError(f"Line {index}: invalid origin")
    if row["consent"] is not True:
        raise ValueError(f"Line {index}: explicit aggregate consent is required")
    if type(row["os"]) is not str or row["os"] not in VALID_OS:
        raise ValueError(f"Line {index}: invalid OS")
    for key in ("setup_success", "false_verified_claim"):
        if type(row[key]) is not bool:
            raise ValueError(f"Line {index}: {key} must be boolean")
    for key in ("would_use_again", "repeat_after_7_days"):
        if row[key] is not None and type(row[key]) is not bool:
            raise ValueError(f"Line {index}: {key} must be boolean or null")
    if type(row["handoff_mode"]) is not str or row["handoff_mode"] not in ("self", "ai", "both", "not_attempted"):
        raise ValueError(f"Line {index}: invalid handoff_mode")
    val = row["setup_minutes"]
    if val is not None and (type(val) not in (int, float) or not 0 <= val <= 120):
        raise ValueError(f"Line {index}: setup_minutes outside bounds")
    val = row["handoff_answers_correct"]
    if val is not None and (type(val) is not int or not 0 <= val <= 5):
        raise ValueError(f"Line {index}: handoff_answers_correct must be 0..5 or null")
    return row


def _no_duplicate_keys(pairs: list[tuple]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def read_reports(path: Path | None) -> list[dict]:
    if path is None:
        return []
    if path.is_symlink() or not path.is_file():
        raise ValueError("Input must be a regular, non-symlink file")
    if path.stat().st_size > MAX_BYTES:
        raise ValueError("Input is too large")
    raw = path.read_bytes()
    if len(raw) > MAX_BYTES:
        raise ValueError("Input is too large")
    try:
        lines = raw.decode("utf-8").splitlines()
    except UnicodeError as exc:
        raise ValueError("Input must be UTF-8") from exc
    if len(lines) > MAX_ROWS:
        raise ValueError("Too many study records")
    reports = []
    seen = set()
    for i, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            row = json.loads(
                line,
                object_pairs_hook=_no_duplicate_keys,
                parse_constant=lambda value: (_ for _ in ()).throw(ValueError("Non-finite number")),
            )
        except (ValueError, TypeError, RecursionError) as exc:
            raise ValueError(f"Line {i}: invalid JSON") from exc
        row = _validate(row, i)
        if row["study_id"] in seen:
            raise ValueError("Duplicate respondent; do not double-count repeat submissions")
        seen.add(row["study_id"])
        reports.append(row)
    return reports


def summarize(reports: list[dict]) -> dict:
    real = [r for r in reports if r["origin"] == "external"]
    n = len(real)
    setup = sum(r["setup_success"] for r in real)
    answers = [r["handoff_answers_correct"] for r in real if r["handoff_answers_correct"] is not None]
    repeat = [r["repeat_after_7_days"] for r in real if r["repeat_after_7_days"] is not None]
    reuse = [r["would_use_again"] for r in real if r["would_use_again"] is not None]
    minutes = [r["setup_minutes"] for r in real if r["setup_minutes"] is not None]
    safety = sum(r["false_verified_claim"] for r in real)
    conditions = {
        "at_least_8_independent_testers": n >= 8,
        "at_least_2_operating_systems": len({r["os"] for r in real}) >= 2,
        "setup_success_at_least_75_percent": n >= 8 and setup / n >= .75,
        "handoff_accuracy_at_least_80_percent": len(answers) >= 8 and sum(answers) / (5 * len(answers)) >= .8,
        "no_reported_false_verification": n >= 8 and safety == 0,
        "at_least_3_week_later_responses": len(repeat) >= 3,
    }
    status = ("NO_EXTERNAL_EVIDENCE" if n == 0 else
              "INVESTIGATE_SAFETY" if safety else
              "READY_FOR_MANUAL_REVIEW" if all(conditions.values()) else
              "COLLECTING")
    return {
        "status": status,
        "independent_testers": n,
        "internal_runs_excluded": len(reports) - n,
        "setup_success": {"count": setup, "total": n},
        "median_setup_minutes": statistics.median(minutes) if minutes else None,
        "handoff_answers": {"correct": sum(answers), "possible": 5 * len(answers)},
        "handoff_modes": {mode: sum(r["handoff_mode"] == mode for r in real) for mode in ("self", "ai", "both", "not_attempted")},
        "reported_false_verified_claims": safety,
        "would_reuse": {"yes": sum(reuse), "respondents": len(reuse)},
        "repeat_after_7_days": {"yes": sum(repeat), "respondents": len(repeat)},
        "acceptance_checks": conditions,
        "warning": "Self-reported pilot feedback, not proof of correctness or product-market fit. Human review required.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize opt-in RepoContinuity pilot results offline")
    parser.add_argument("--input", type=Path, help="Local JSONL of explicitly consented observations")
    args = parser.parse_args(argv)
    try:
        result = summarize(read_reports(args.input))
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
