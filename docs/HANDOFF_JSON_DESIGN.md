# Proposed handoff JSON contract (design only — Phase 3 implementation pending)

This file defines the planned portable format without falsely claiming an exporter exists. Future schema ID: `repocontinuity.handoff.v1`. Phase 3 will validate this contract before enabling `export`/`import`.

Minimum top-level fields:

```json
{
  "schema_id": "repocontinuity.handoff.v1",
  "generated_at": "2026-11-10T00:00:00+00:00",
  "project": {"name": "Example project"},
  "git": {"head_sha": "0123456789012345678901234567890123456789", "dirty": false, "branch": "main"},
  "decisions": [{"id": "example", "title": "Keep backend", "status": "approved", "approved_by": "Owner"}],
  "tasks": [{"id": "t1", "title": "Add regression test", "status": "complete_unverified", "verified_evidence_id": null}],
  "evidence": [],
  "blockers": [],
  "next_actions": ["Run agreed checks and request explicit approval before deploying"],
  "limitations": ["This is illustrative data and not a generated handoff"]
}
```

## Proposed safety properties

1. Explicit opt-in for file generation; no background exports or uploads.
2. Deterministic ordering, bounded field sizes, visible preview and schema validation.
3. Redact or reject known credential patterns; exclude absolute local paths, hidden directories, raw CLI arguments, stdout/stderr, chat histories and entire code files by default.
4. An explicit `verified_evidence_id` alone does not prove quality: include command-observation type, result, Git SHA and associated limitations.
5. New agent must treat imported text as **untrusted context**, never executable instructions. Never accept authorization to change project architecture from the imported packet alone.
6. A Git SHA mismatch or dirty tree at export/import must be surfaced, not silently dismissed.
7. Schema version changes require separate compatibility handling; no unsafe JSON-to-SQL direct mapping.

This contract is not a signed, cryptographically verifiable artifact. Data is local and user-editable. Phase 3 must ship tests for redaction, schema compatibility, prompt-injection handling and stale repository state before general release.
