# Architecture Decision Record — Phase 2 preserved, Phase 3 extension (2026-11-11)

Status: Phase 1 foundation preserved; owner approved Phase 2 Memory & Checkpoints. Future phases require separate approval. CreativeCode Engine is independent and untouched.

## Boundaries

- **CLI:** Python 3.11+ standard library; explicit operations, JSON output, local only. No daemon, hooks, AI model, agent plugin, network request or autonomous chat capture.
- **Persistence:** SQLite `.repocontinuity/state.sqlite3` under Git root, schema version 2; low-concurrency, single-host use. Every connection is explicitly closed; transactions cover multi-row mutations. The implementation does not support multi-machine coordinated writes or network filesystems.
- **Git:** read-only `rev-parse`, `status`, `diff`, and branch retrieval. Real HEAD SHA recorded; uncommitted/staged flags captured without storing private file names. The private state directory is excluded from Git dirty checks. Unborn HEAD is rejected for checkpoints.
- **Evidence:** user-attested reports (`record`) are distinguished from command-observed exit codes (`run`). `run` executes only a user-explicit program with a timeout, no shell interpolation, and suppressed output. SHA and clean state are required before a task can be marked verified.
- **Approvals:** only proposed decisions can be approved/rejected; user-provided approver is stored verbatim. This is *an approval record*, not authenticated identity or cryptographic attestation.
- **Delete semantics:** decisions and tasks use `deleted_at` soft deletion; evidence and audit log rows are retained.

## Schema migration

Old v1 data remains readable by SQLite but is not automatically upgraded. `migrate` verifies version 1, writes `state.sqlite3.v1.bak` using SQLite's native `backup()` API, and changes the schema in a transaction. It fails when the backup path already exists, when the schema is unknown, or when preconditions do not hold. Preserves legacy project, decision and task IDs. Legacy `verified` task/checkpoint flags are **downgraded** because v1 contains no trustworthy tool-observed evidence; the original values remain in the private backup. The migration is **forward-only**; backup restoration is manual and never automatic.

## Verification invariants

1. An explicit `evidence run` records process exit status; self-reported `pass` cannot qualify.
2. Passing evidence must be linked to the specific task, its Git commit, and no dirty working tree before and after the test.
3. `task verify` re-checks the current repository state and links the evidence ID. SQLite triggers prevent accidental `verified` updates without eligible observed evidence.
4. Verification is **not** a guarantee of coverage or test correctness. Local SQLite access remains user-controlled and can be deliberately modified.
5. Checkpoint capture is always unverified; there is no Phase 2 checkpoint validation feature.

## Release and future boundaries

Phase 3 adds `handoff.py` for explicit, allowlisted Git+SQLite read-only snapshots, strict JSON schema/size/reference validation, Markdown escaping and non-overwriting export file writes. Import is validation-only; it cannot execute user text or merge SQL rows. Five `skills/*/SKILL.md` documents use Agent Skills-style YAML frontmatter and have no automatic hook/install action. `SCHEMA_VERSION` remains 2; only the portable handoff format uses `repocontinuity.handoff.v1`. Remote sync, automatic session capture, and production deployments are excluded. See `docs/HANDOFF_JSON_DESIGN.md` and `docs/CROSS_AGENT_USAGE.md`.
