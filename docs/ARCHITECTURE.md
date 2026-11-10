# Architecture Decision Record — Phase 1 (2026-11-10)

Status: proposed architecture implemented as a local scaffold; later phases require separate approval.

## Scope and boundaries

RepoContinuity is an independent repository. It must never modify CreativeCode Engine, existing project architectures or user project source files. The CLI starts with read-only `doctor` and explicit `init`. No daemon, hook, AI API, auto-sync, or cloud component ships in Phase 1.

### Modules

1. `cli.py` — command routing and machine-readable doctor output.
2. `gitinfo.py` — read-only discovery of the Git working tree with argument-array subprocess invocation and timeout.
3. `storage.py` — versioned SQLite schema; creates only opt-in project state directory.
4. `docs/` — data contract, security requirements and roadmap.
5. `tests/` — stdlib unit tests in isolated temporary directories.

## Storage

`<git-root>/.repocontinuity/state.sqlite3` is local-only by default. SQLite is suitable for single-user and low-write concurrency; it requires no additional server. WAL and shared network filesystem operation are not enabled. Future parallel agents require explicit serialized writes or a revised coordination layer; **do not assume SQLite offers multi-machine coordination**.

Tables: `schema_meta`, `projects`, `decisions`, `tasks`, `evidence`, `checkpoints`. The v1 schema defines constrained statuses but not the business rules for transitions. Phase 2 must enforce that `verified` requires an actual passing evidence reference and must treat verbal AI claims as unverified.

## Provenance contract

Every future handoff must state:

- last observed Git SHA and whether the tree was dirty;
- which decisions are approved and by whom;
- which tasks were completed versus independently verified;
- evidence references and exact checks performed;
- known blockers, missing evidence and next allowed actions.

**Evidence is not equivalent to a claim.** Git SHAs, test logs and timestamps are traceability metadata; verification still depends on actual test results and their scope.

## Format and portability

SQLite is the private operational store, not the interchange format. Future explicit Markdown+JSON export uses versioned schemas, redaction, bounded output and deterministic order. No silent export of `.env`, API tokens, files or conversations.

## Versioning and migrations

`schema_meta.version = 1`. No auto-migration; unknown schema versions fail closed. Future migrations require backup and reversible test fixtures.

## Definition of done for Phase 1

- local skeleton with `init`/`doctor`;
- tests validating no writes on doctor, idempotent init, schema version and FK constraints;
- CI config and docs;
- repository created and pushed **only when authenticated creation permissions exist**;
- no claims of production handoff in this phase.
