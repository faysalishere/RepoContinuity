# RepoContinuity

**Approval-aware, evidence-linked local project memory for AI-assisted coding.**

[![CI](https://github.com/faysalishere/RepoContinuity/actions/workflows/ci.yml/badge.svg)](https://github.com/faysalishere/RepoContinuity/actions/workflows/ci.yml)

**Current status: `v0.4.0b1` (Phase 4 public-beta candidate).** RepoContinuity provides an explicit local CLI for project decisions, tasks, observed test outcomes, Git checkpoints and **versioned JSON/Markdown handoffs**. Five reusable, model-agnostic Agent Skills are included. **No automatic chat reading, session transfer, remote sync, model integration, or production-readiness certification.**

## Phase 5 — Independent user validation (open for feedback)

**Seeking real testers.** Try the [10–15 minute, consent-based pilot](docs/USER_STUDY.md) and submit sanitized feedback via [GitHub's user-study issue form](https://github.com/faysalishere/RepoContinuity/issues/new/choose). A [fictional sample handoff](examples/study_handoff.md) and [answer key](docs/STUDY_ANSWER_KEY.md) help test context fidelity without sharing a real project. The [scorecard](docs/VALIDATION_METRICS.md) defines success and failure criteria **before** reports arrive. [Current validation status](docs/VALIDATION_STATUS.md): no independent participant results have yet been verified.

The CLI remains local and opt-in; no analytics or report uploads are built in. Independent survey feedback should not be mistaken for an official GitHub pre-release: the `v0.4.0b1` tag/release is still pending.

## What is different?

A chat summary can say "done" even when no test ran. RepoContinuity deliberately separates:

- **Proposed vs approved decisions:** approvals require a named human approver (self-attested; no identity authentication).
- **Completed vs verified tasks:** `verified` requires a recorded passing command executed by the tool, tied to the same clean Git commit. A manual success claim alone never qualifies.
- **Git provenance:** explicit checkpoints capture the real commit SHA, branch and dirty/staged flags, without logging source paths.
- **Local-first privacy:** SQLite in the repository's private, Git-ignored `.repocontinuity` directory; no cloud accounts, API calls or telemetry.

Verification means an explicitly selected command returned exit code 0 for a clean Git state. It **does not** mean the test command covers all behavior, or that the contents of the local SQLite database are tamper-proof.

## Quick start

**New:** [2-minute safe interactive demo](docs/QUICK_START.md) runs in a disposable Git repo and never modifies your real project. Run `python examples/quickstart_demo.py` after installing from source.


Requires Python 3.11+ and Git. No third-party Python runtime dependencies.

```bash
git clone https://github.com/faysalishere/RepoContinuity.git
cd RepoContinuity
python -m pip install -e .
repocontinuity doctor
repocontinuity init
repocontinuity checkpoint capture
```

The commands work for any existing Git project after installation: `cd /path/to/project && repocontinuity init`. Do not initialize a production project without first reviewing its repository status and desired local state location.

### Record an explicitly approved decision

```bash
repocontinuity decision add --title "Preserve existing architecture" --rationale "No approved rewrite"
repocontinuity decision list
# Copy the returned ID, then:
repocontinuity decision approve --id DECISION_ID --by "Project owner"
```

Approval identity is a user-provided label, not cryptographic identity verification. Approved decisions cannot be silently edited by the CLI.

### Track a task and execute an explicit test

```bash
repocontinuity task add --title "Add regression tests"
repocontinuity task status --id TASK_ID --status complete_unverified
# The following executes the command you supply — only use trusted test commands.
repocontinuity evidence run --task-id TASK_ID -- python -m unittest discover -s tests
repocontinuity task verify --id TASK_ID --evidence-id EVIDENCE_ID
```

A task can be verified only when the test was executed and passed on the **same clean commit**. Code produced by a tool or a user-supplied `pass` flag is not sufficient. `evidence run` executes the specified program **with your current user's permissions**; review it first. The command's output is discarded and never added to the database. Only its exit status, commit state and a hash of its argument vector are recorded. Do not include secrets in commands.

### Export a portable handoff (Phase 3)

```bash
# JSON to stdout, so you can preview and redact before sharing:
repocontinuity handoff export --format json

# Explicit file output (must not already exist; do not commit it blindly):
repocontinuity handoff export --format json --out handoff.json
repocontinuity handoff export --format markdown --out handoff.md

# Validation-only import preflight; NEVER executes embedded text or writes SQLite:
repocontinuity handoff validate --file handoff.json
repocontinuity handoff import --file handoff.json
```

Handoff schema: `repocontinuity.handoff.v1`. JSON is structured portable **untrusted data**, Markdown is for human review. `import` is deliberately an alias for **read-only preflight validation**, not an importer that merges approvals or tasks. The validation report flags stale SHA, Git dirty state and common instruction-like text. All incoming packets require human review even if their structural checks pass. All imported approvals and evidence remain untrusted until independently rechecked. The exporter downgrades stale `verified` task status to `complete_unverified` without changing your SQLite database. 

Export uses an allowlist and best-effort redaction of common credentials, paths and email addresses, with size/record limits. **Redaction is not comprehensive**: always review private notes before sharing or committing handoffs. Writing an export inside the repo makes the worktree dirty; run a new status check before trusting a snapshot. Handoff files are never automatically committed, uploaded or installed anywhere.

### Five reusable, model-agnostic Agent Skills

The `skills/` directory contains independent Agent Skills: `research-first`, `minimal-change`, `systematic-debugging`, `verification-gates`, and `project-continuity-handoff`. These are plain `SKILL.md` files with Agent Skills standard frontmatter. They **do not** auto-install themselves or run hooks. Use your coding assistant's documented skill-loading/import mechanism, or provide the content manually. See [cross-agent guidance](docs/CROSS_AGENT_USAGE.md).

### Existing Phase 1 users: migrate explicitly

A Phase 1 project has database schema v1. `init` will not silently upgrade it.

```bash
repocontinuity doctor
repocontinuity migrate
repocontinuity doctor
```

Migration first creates a protected local SQLite backup named `state.sqlite3.v1.bak` and preserves old decisions/tasks. Legacy `verified` flags are intentionally downgraded to `complete_unverified`/`unverified`, because v1 had no observed test evidence. Backups are not uploaded or committed. For unexpected migration errors, inspect your backup and seek help rather than deleting anything.

## Command reference

| Area | Commands |
|---|---|
| Diagnostics | `doctor`, `init`, `migrate` |
| Decisions | `decision add/list/update/approve/reject/remove` |
| Tasks | `task add/list/update/status/verify/remove` |
| Evidence | `evidence record/run/list` |
| Git checkpoints | `checkpoint capture/list` |
| Handoff | `handoff export/validate/import` (`import` is validation-only) |

Run `repocontinuity <group> <command> --help` for exact flags. Removals are **soft deletes** requiring `--confirm`; include them using `list --all`. Manual evidence (`record`) is preserved for traceability but can never independently set a task to `verified`. `checkpoint capture` itself always records `unverified`, because a checkpoint validation workflow is not included yet.

## Architecture, scope and security

- [Architecture and Git/SQLite design](docs/ARCHITECTURE.md)
- [SQLite v2 data contract](docs/DATA_CONTRACT.md)
- [Implemented JSON handoff contract](docs/HANDOFF_JSON_DESIGN.md)
- [Cross-agent usage and trust boundaries](docs/CROSS_AGENT_USAGE.md)
- [Security model and command execution warning](docs/SECURITY_MODEL.md)
- [Competition and naming audit](docs/COMPETITORS.md)
- [Phase-gated roadmap](docs/ROADMAP.md)

## Testing

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

GitHub Actions tests Python 3.11–3.13 on Ubuntu, macOS and Windows. Until the current CI run is green, cross-platform support for this change is not verified. The project is a **public-beta candidate**; do not rely on it as a compliance platform or authoritative security audit. See [release notes](RELEASE_NOTES.md), [release process](docs/RELEASE_PROCESS.md) and [security audit](docs/SECURITY_AUDIT.md).

MIT licensed. See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).
