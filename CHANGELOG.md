# Changelog

## 0.1.0a1 — Phase 1 foundation (2026-11-10)

- Initialized a stand-alone repository structure for RepoContinuity.
- Added read-only `doctor` and explicit `init` commands.
- Added private local SQLite schema v1 for projects, decisions, tasks, evidence and checkpoints.
- Added safe Git root lookup, idempotent initialization and schema fail-closed behavior.
- Added isolated Python standard-library tests and cross-platform GitHub Actions CI configuration.
- Documented market overlap, security boundaries, roadmap and data contract.

**Not released:** No public GitHub repository or package registry release is implied by this file.

## 0.2.0a1 — Phase 2: Memory & Checkpoints (2026-11-10)

- Added explicit decision/task management with approvals and soft deletions.
- Added observed test evidence and evidence-linked task verification for clean Git commits.
- Added Git SHA checkpoints with dirty/staged flags and no captured private paths.
- Added SQLite schema v2 and explicit v1-to-v2 migration with protected local backup.
- Added checks to downgrade unsubstantiated legacy verification and reject accidental false verification.
- Documented the proposed Phase 3 JSON handoff format; no exporter ships yet.
