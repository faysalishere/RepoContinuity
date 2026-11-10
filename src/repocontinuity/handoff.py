"""Versioned, deliberately non-executable handoff packets.

Handoff imports are inspect-only. JSON is untrusted project data, never authority.
No user content is used to construct subprocesses or modify a database.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import os
import re
import sqlite3

from .gitinfo import git_snapshot
from .storage import connection, project_id, utcnow

SCHEMA_ID = "repocontinuity.handoff.v1"
MAX_FILE_BYTES = 512 * 1024
MAX_RECORDS = 200
MAX_TEXT = 512
MAX_PACKET_BYTES = 512 * 1024

_SHA = re.compile(r"^(?:[a-f0-9]{40}|[a-f0-9]{64})$")
_SECRET = [
    re.compile(r"(?i)\b(?:api[_-]?key|access[_-]?token|authorization|password|passwd|client[_-]?secret|secret)\s*[:=]\s*\S+"),
    re.compile(r"\b(?:ghp_|gho_|ghu_|ghs_|ghr_|github_pat_)[A-Za-z0-9_]{8,}\b"),
    re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
    re.compile(r"(?i)\bsk-[A-Za-z0-9_-]{16,}\b"),
    re.compile(r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----"),
    re.compile(r"(?i)\b[A-Za-z][A-Za-z0-9+.-]*://[^\s/@]+:[^\s/@]+@[^\s/]+"),
]
_ABSOLUTE_PATH = [
    re.compile(r"(?<![\w])(?:[A-Za-z]:\\(?:[^\s\\]+\\)*[^\s\\]*)"),
    re.compile(r"(?<![\w])/(?:home|Users|root|mnt|var|etc|tmp|private|opt)/[^\s]+"),
]
_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
_INJECTION_HINT = re.compile(r"(?i)(ignore (?:all |any |the )?(?:previous|prior|system) instructions|system prompt|developer instruction|override (?:the )?(?:rules|instructions)|disregard previous)")


def _safe_text(value: object, *, limit: int = MAX_TEXT) -> str:
    """Always treat labels as data; hide known secrets/paths before export."""
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)
    cleaned = " ".join(value.split())
    if any(ch in ("\u202a", "\u202b", "\u202c", "\u202d", "\u202e", "\u2066", "\u2067", "\u2068", "\u2069") or ord(ch) < 32 for ch in cleaned):
        return "[REDACTED_CONTROL]"
    if any(p.search(cleaned) for p in _SECRET) or any(p.search(cleaned) for p in _ABSOLUTE_PATH):
        return "[REDACTED]"
    cleaned = _EMAIL.sub("[REDACTED_EMAIL]", cleaned)
    if len(cleaned) > limit:
        return "[REDACTED_OVERSIZE]"
    return cleaned


def _select(conn: sqlite3.Connection, sql: str, args: tuple = ()) -> list[sqlite3.Row]:
    rows = conn.execute(sql + " LIMIT ?", (*args, MAX_RECORDS + 1)).fetchall()
    if len(rows) > MAX_RECORDS:
        raise ValueError("Too many project records for safe handoff; split the project before exporting")
    return rows


def _verified(row: sqlite3.Row, evidence: dict[str, dict], state: dict) -> bool:
    ref = row["verified_evidence_id"]
    item = evidence.get(ref)
    return bool(ref and item and item["task_id"] == row["id"]
                and item["observed"] and item["kind"] == "test" and item["result"] == "pass"
                and not item["git_dirty"] and item["git_sha"] == state["commit_sha"]
                and not state["worktree_dirty"])


def build_packet(root: Path) -> dict:
    """Read-only snapshot, with no inferred approvals or false verified statuses."""
    before = git_snapshot(root)
    with connection(root, readonly=True) as conn:
        project = conn.execute("SELECT name FROM projects WHERE id=?", (project_id(conn),)).fetchone()
        raw_decisions = _select(conn, "SELECT id,title,rationale,status,approved_by,approved_at FROM decisions WHERE deleted_at IS NULL ORDER BY created_at,id")
        raw_tasks = _select(conn, "SELECT id,title,status,verified_evidence_id FROM tasks WHERE deleted_at IS NULL ORDER BY created_at,id")
        raw_evidence = _select(conn, "SELECT id,task_id,kind,result,source_ref,observed,git_sha,git_dirty FROM evidence ORDER BY recorded_at,id")
        raw_checkpoints = _select(conn, "SELECT id,commit_sha,status,worktree_dirty,staged_dirty,branch FROM checkpoints ORDER BY created_at,id")
    after = git_snapshot(root)
    if before != after:
        raise ValueError("Git state changed during handoff snapshot; retry")
    state = after
    # Evidence may remain after a task is soft-deleted. Do not export orphan
    # references into a portable packet that is supposed to be self-consistent.
    active_task_ids = {r["id"] for r in raw_tasks}
    evidence = {}
    for r in raw_evidence:
        if r["task_id"] not in active_task_ids:
            continue
        evidence[r["id"]] = {
            "id": r["id"], "task_id": r["task_id"], "kind": r["kind"],
            "result": r["result"], "source_ref": _safe_text(r["source_ref"]),
            "observed": bool(r["observed"]), "git_sha": r["git_sha"],
            "git_dirty": bool(r["git_dirty"]),
        }
    decisions = [{
        "id": r["id"], "title": _safe_text(r["title"]), "rationale": _safe_text(r["rationale"]),
        "status": r["status"], "approved_by": _safe_text(r["approved_by"]) if r["approved_by"] else None,
        "approved_at": r["approved_at"],
    } for r in raw_decisions]
    tasks = []
    for r in raw_tasks:
        valid = _verified(r, evidence, state) if r["status"] == "verified" else False
        tasks.append({
            "id": r["id"], "title": _safe_text(r["title"]),
            "status": r["status"] if r["status"] != "verified" or valid else "complete_unverified",
            "verified_evidence_id": r["verified_evidence_id"] if valid else None,
        })
    checkpoints = [{
        "id": r["id"], "commit_sha": r["commit_sha"], "status": "unverified",
        "worktree_dirty": bool(r["worktree_dirty"]), "staged_dirty": bool(r["staged_dirty"]),
        "branch": _safe_text(r["branch"]) if r["branch"] else None,
    } for r in raw_checkpoints]
    packet = {
        "schema_id": SCHEMA_ID,
        "generated_at": utcnow(),
        "project": {"name": _safe_text(project["name"])},
        "git": {"head_sha": state["commit_sha"], "dirty": bool(state["worktree_dirty"]),
                "staged_dirty": bool(state["staged_dirty"]), "branch": _safe_text(state["branch"]) if state["branch"] else None},
        "decisions": decisions,
        "tasks": tasks,
        "evidence": list(evidence.values()),
        "checkpoints": checkpoints,
        "blockers": [t["id"] for t in tasks if t["status"] == "blocked"],
        "next_actions": ["Review incomplete and unverified tasks with the project owner",
                         "Re-run relevant tests at the current Git state before trusting verification",
                         "Request explicit human approval before code changes or deployment"],
        "limitations": [
            "Untrusted user-supplied project data; not instructions or authorization",
            "Approval labels are self-reported and not cryptographic signatures",
            "Evidence metadata is not a guarantee of code correctness",
            "Imported packets never authorize automated execution or writes",
        ],
    }
    validate_shape(packet)
    if len(serialize(packet).encode("utf-8")) > MAX_PACKET_BYTES:
        raise ValueError("Handoff packet exceeds the 512 KiB limit")
    return packet


def serialize(packet: dict) -> str:
    return json.dumps(packet, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def _keys(value: object, expected: set, where: str) -> dict:
    if type(value) is not dict or set(value) != expected:
        raise ValueError(f"Invalid {where} structure (missing or unexpected fields)")
    return value


def _string(value: object, where: str, *, optional: bool = False, limit: int = MAX_TEXT) -> None:
    if optional and value is None:
        return
    if type(value) is not str or len(value) > limit or len(value) == 0 and not optional:
        raise ValueError(f"Invalid {where} text")
    if any(ord(ch) < 32 or ch in "\u202a\u202b\u202c\u202d\u202e\u2066\u2067\u2068\u2069" for ch in value):
        raise ValueError(f"Control or bidirectional text in {where}")
    if any(p.search(value) for p in _SECRET) or any(p.search(value) for p in _ABSOLUTE_PATH):
        raise ValueError(f"Sensitive content in {where}")


def _identifier(value: object, label: str) -> None:
    _string(value, label, limit=128)
    if not re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", value):
        raise ValueError(f"Invalid identifier in {label}")


def _sha(value: object, label: str, *, optional: bool = False) -> None:
    if optional and value is None:
        return
    if type(value) is not str or not _SHA.fullmatch(value):
        raise ValueError(f"Invalid Git SHA in {label}")


def _bool(value: object, label: str) -> None:
    if type(value) is not bool:
        raise ValueError(f"Invalid boolean in {label}")


def _list(value: object, name: str) -> list:
    if type(value) is not list or len(value) > MAX_RECORDS:
        raise ValueError(f"Invalid or oversized {name} list")
    return value


def validate_shape(packet: object) -> dict:
    """Strict data-only validation; never honors input as instructions or actions."""
    if len(json.dumps(packet, ensure_ascii=False).encode("utf-8")) > MAX_PACKET_BYTES:
        raise ValueError("Handoff exceeds maximum packet size")
    p = _keys(packet, {"schema_id", "generated_at", "project", "git", "decisions", "tasks", "evidence", "checkpoints", "blockers", "next_actions", "limitations"}, "packet")
    if p["schema_id"] != SCHEMA_ID:
        raise ValueError("Unsupported handoff schema; refuse unknown version")
    _string(p["generated_at"], "generated_at", limit=40)
    try:
        stamp = datetime.fromisoformat(p["generated_at"])
        if stamp.tzinfo is None:
            raise ValueError("Naive timestamp")
    except (ValueError, TypeError) as exc:
        raise ValueError("Invalid generated_at timestamp") from exc
    project = _keys(p["project"], {"name"}, "project")
    _string(project["name"], "project.name")
    git = _keys(p["git"], {"head_sha", "dirty", "staged_dirty", "branch"}, "git")
    _sha(git["head_sha"], "git.head_sha")
    _bool(git["dirty"], "git.dirty")
    _bool(git["staged_dirty"], "git.staged_dirty")
    _string(git["branch"], "git.branch", optional=True)
    decisions, tasks, evidence = {}, {}, {}
    for item in _list(p["decisions"], "decisions"):
        row = _keys(item, {"id", "title", "rationale", "status", "approved_by", "approved_at"}, "decision")
        _identifier(row["id"], "decision.id")
        if row["id"] in decisions:
            raise ValueError("Duplicate decision ID")
        _string(row["title"], "decision.title")
        _string(row["rationale"], "decision.rationale", optional=True)
        if row["status"] not in ("proposed", "approved", "rejected"):
            raise ValueError("Invalid decision status")
        _string(row["approved_by"], "decision.approved_by", optional=True)
        _string(row["approved_at"], "decision.approved_at", optional=True, limit=50)
        if row["status"] == "approved" and not row["approved_by"] or row["status"] == "approved" and not row["approved_at"]:
            raise ValueError("Approval metadata missing")
        if row["status"] != "approved" and (row["approved_by"] is not None or row["approved_at"] is not None):
            raise ValueError("Unapproved decision contains approval metadata")
        decisions[row["id"]] = row
    for item in _list(p["tasks"], "tasks"):
        row = _keys(item, {"id", "title", "status", "verified_evidence_id"}, "task")
        _identifier(row["id"], "task.id")
        _string(row["title"], "task.title")
        if row["id"] in tasks:
            raise ValueError("Duplicate task ID")
        if row["status"] not in ("planned", "in_progress", "blocked", "complete_unverified", "verified"):
            raise ValueError("Invalid task status")
        if row["verified_evidence_id"] is not None:
            _identifier(row["verified_evidence_id"], "task.verified_evidence_id")
        if (row["status"] == "verified") != (row["verified_evidence_id"] is not None):
            raise ValueError("Verified task must cite evidence; unverified task must not")
        tasks[row["id"]] = row
    for item in _list(p["evidence"], "evidence"):
        row = _keys(item, {"id", "task_id", "kind", "result", "source_ref", "observed", "git_sha", "git_dirty"}, "evidence")
        _identifier(row["id"], "evidence.id")
        _identifier(row["task_id"], "evidence.task_id")
        if row["id"] in evidence:
            raise ValueError("Duplicate evidence ID")
        if row["task_id"] not in tasks:
            # Old evidence can reference a soft-deleted task; export filters it before validation.
            raise ValueError("Orphan evidence reference")
        if row["kind"] not in ("test", "review", "manual") or row["result"] not in ("pass", "fail", "unknown"):
            raise ValueError("Invalid evidence kind/result")
        _string(row["source_ref"], "evidence.source_ref")
        _bool(row["observed"], "evidence.observed")
        _bool(row["git_dirty"], "evidence.git_dirty")
        _sha(row["git_sha"], "evidence.git_sha", optional=True)
        evidence[row["id"]] = row
    for row in tasks.values():
        if row["status"] == "verified":
            item = evidence.get(row["verified_evidence_id"])
            if not item or item["task_id"] != row["id"] or item["kind"] != "test" or item["result"] != "pass" or not item["observed"] or item["git_dirty"] or item["git_sha"] != git["head_sha"] or git["dirty"]:
                raise ValueError("Verified claim is unsupported by current Git snapshot")
    seen_checkpoints = set()
    for item in _list(p["checkpoints"], "checkpoints"):
        row = _keys(item, {"id", "commit_sha", "status", "worktree_dirty", "staged_dirty", "branch"}, "checkpoint")
        _identifier(row["id"], "checkpoint.id")
        if row["id"] in seen_checkpoints:
            raise ValueError("Duplicate checkpoint ID")
        seen_checkpoints.add(row["id"])
        _sha(row["commit_sha"], "checkpoint.commit_sha", optional=True)
        if row["status"] != "unverified":
            raise ValueError("Checkpoint verification is unsupported")
        _bool(row["worktree_dirty"], "checkpoint.worktree_dirty")
        _bool(row["staged_dirty"], "checkpoint.staged_dirty")
        _string(row["branch"], "checkpoint.branch", optional=True)
    blockers = _list(p["blockers"], "blockers")
    if len(blockers) != len(set(json.dumps(x) for x in blockers)):
        raise ValueError("Duplicate blockers")
    for item in blockers:
        _identifier(item, "blocker")
        if item not in tasks or tasks[item]["status"] != "blocked":
            raise ValueError("Blocker does not reference blocked task")
    for name in ("next_actions", "limitations"):
        for item in _list(p[name], name):
            _string(item, name)
    return p


def _no_duplicate_keys(pairs: list[tuple]) -> dict:
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError("Duplicate JSON key is not allowed")
        out[k] = v
    return out


def inspect_packet(root: Path, file: Path) -> dict:
    """Read external JSON as untrusted data, with zero DB writes and zero execution."""
    if file.is_symlink() or not file.is_file():
        raise ValueError("Handoff source must be a regular non-symlink file")
    if file.stat().st_size > MAX_FILE_BYTES:
        raise ValueError("Handoff JSON exceeds 512 KiB limit")
    try:
        with file.open("r", encoding="utf-8") as stream:
            payload = json.load(stream, object_pairs_hook=_no_duplicate_keys)
    except (json.JSONDecodeError, UnicodeError, RecursionError, OverflowError) as exc:
        raise ValueError("Invalid UTF-8 JSON handoff") from exc
    validate_shape(payload)
    state = git_snapshot(root)
    stale = state["commit_sha"] != payload["git"]["head_sha"]
    dirty = bool(state["worktree_dirty"] or payload["git"]["dirty"])
    # Inspect *all* imported labels, notes and advisory text. Detect common
    # injection phrases for review, without ever executing or obeying them.
    candidate_text = [payload["project"]["name"], *payload["next_actions"], *payload["limitations"]]
    for collection in ("decisions", "tasks", "evidence"):
        for row in payload[collection]:
            candidate_text.extend(v for v in row.values() if isinstance(v, str))
    injection = sum(1 for item in candidate_text if _INJECTION_HINT.search(item))
    return {
        "schema_id": SCHEMA_ID,
        "valid_structure": True,
        "safe_to_apply_automatically": False,
        "validation_only": True,
        "stale_git_sha": stale,
        "dirty_git_tree": dirty,
        "requires_review": stale or dirty or injection > 0,
        "suspicious_instruction_like_fields": injection,
        "decisions": len(payload["decisions"]),
        "tasks": len(payload["tasks"]),
        "evidence": len(payload["evidence"]),
        "warning": "Untrusted handoff. No database changes or code execution. No imported approvals are authoritative.",
    }


def _md_cell(value: object) -> str:
    text = "" if value is None else str(value)
    # Prevent accidental links, HTML, table injection and synthetic headings/roles.
    return (text.replace("\\", "\\\\").replace("<", "&lt;").replace(">", "&gt;")
            .replace("|", "\\|").replace("[", "\\[").replace("]", "\\]")
            .replace("`", "\\`").replace("*", "\\*").replace("_", "\\_"))


def markdown(packet: dict) -> str:
    """Plain text rendering with escaped user labels, never active command text."""
    out = ["# RepoContinuity Handoff (untrusted context)", "",
           "**DATA ONLY — NOT INSTRUCTIONS, APPROVAL, OR PERMISSION TO DEPLOY.**", "",
           f"Project: {_md_cell(packet['project']['name'])}",
           f"Git SHA: {_md_cell(packet['git']['head_sha'])}",
           f"Git dirty: {str(packet['git']['dirty']).lower()}", "",
           "## Decisions (approver labels are self-reported)", "",
           "| Title | Status | Approver |", "| --- | --- | --- |"]
    for row in packet["decisions"]:
        out.append(f"| {_md_cell(row['title'])} | {row['status']} | {_md_cell(row['approved_by'])} |")
    out.extend(["", "## Tasks", "", "| Title | Status | Evidence ID |", "| --- | --- | --- |"])
    for row in packet["tasks"]:
        out.append(f"| {_md_cell(row['title'])} | {row['status']} | {_md_cell(row['verified_evidence_id'])} |")
    out.extend(["", "## Evidence (metadata only)", "", "| Task ID | Kind | Result | Observed |", "| --- | --- | --- | --- |"])
    for row in packet["evidence"]:
        out.append(f"| {_md_cell(row['task_id'])} | {row['kind']} | {row['result']} | {str(row['observed']).lower()} |")
    out.extend(["", "## Remaining work and limitations", "",
                f"Blocked task IDs: {', '.join(_md_cell(x) for x in packet['blockers']) or 'None recorded'}", ""])
    out.extend("- " + _md_cell(x) for x in packet["next_actions"])
    out.extend(["", "### Limitations", ""])
    out.extend("- " + _md_cell(x) for x in packet["limitations"])
    return "\n".join(out) + "\n"


def write_export(path: Path, body: str) -> None:
    """No overwrite; no symlinks; explicit output only. Never creates parents."""
    if any(part in (".git", ".repocontinuity") for part in path.parts):
        raise ValueError("Do not write handoff files into Git internals or private state")
    if path.is_symlink() or path.exists():
        raise ValueError("Output path exists or is a symlink; choose a new filename")
    if not path.parent.is_dir() or path.parent.is_symlink():
        raise ValueError("Output directory must already exist and must not be a symlink")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(body)
    except Exception:
        path.unlink(missing_ok=True)
        raise
