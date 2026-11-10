# Approved roadmap — RepoContinuity

Phase changes require owner approval. CreativeCode Engine must remain separate and unchanged.

- **Phase 1 — Foundation & Architecture: COMPLETE.** Competitor/name audit, GitHub repository, Python CLI skeleton, SQLite schema v1, 9/9 cross-platform CI jobs.
- **Phase 2 — Memory & Checkpoints: IMPLEMENTED LOCALLY / CI PENDING.** Explicit decision/task CRUD, approval statuses, observed test evidence + verification constraints, actual Git SHA checkpoints, backed-up SQLite v1→v2 migration and a proposed JSON handoff contract.
- **Phase 3 — AI Handoff & Skills: NOT STARTED.** Versioned Markdown/JSON packets, five reusable SKILL.md workflows, model-agnostic instructions and safe import validation.
- **Phase 4 — Public Release: NOT STARTED.** Production-grade tests, package/release pipeline, interactive quick start, security review, cross-platform compatibility.
- **Phase 5 — Real User Validation: NOT STARTED.** Measure real handoff accuracy, task state loss, incorrect completion claims, setup success, repeat usage and interviews.

## Phase 2 exit checklist

- [x] Preserve Phase 1 CLI, package, schema compatibility and decisions.
- [x] Explicit decision/task create/read/update/soft-delete with approval boundaries.
- [x] Real Git checkpoint capture and dirty/staged state handling.
- [x] Evidence-linked task verification, no auto-claim for user-entered success.
- [x] Explicit database migration with non-overwriting backup and legacy status downgrade.
- [x] Document proposed JSON handoff design (export implementation stays Phase 3).
- [x] Local integration/security tests.
- [ ] GitHub deployment, full 9-job CI and read-back validation.
- [ ] Owner approval before Phase 3.
