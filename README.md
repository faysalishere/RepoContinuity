# RepoContinuity

**Approval-aware, evidence-linked local project memory for AI-assisted coding.**

[![CI](https://github.com/faysalishere/RepoContinuity/actions/workflows/ci.yml/badge.svg)](https://github.com/faysalishere/RepoContinuity/actions/workflows/ci.yml)

**Current status: `v0.2.0a1` — Phase 2 pre-alpha.** RepoContinuity provides an explicit local CLI for project decisions, tasks, test outcomes, SQLite state and Git checkpoints. It **does not automatically read AI conversations, generate cross-agent handoffs, validate code coverage or run background agents.** Those remain future phases in the [approved roadmap](docs/ROADMAP.md).

## What is different?

- **Proposed vs approved decisions:** recording approval requires a named person; this identity is user-attested, not authenticated.
- **Complete vs verified tasks:** a task may be marked `verified` only after an explicitly executed, passing command observed at the same clean Git commit. Manual claims do not qualify.
- **Real repository state:** checkpoints contain an actual Git SHA, branch and staged/dirty flags—not a guessed summary.
- **Local by default:** SQLite state stays inside Git-ignored `.repocontinuity/`, with no cloud API or telemetry.

A zero exit status is limited evidence that a chosen command passed. It is **not proof** that tests cover all behavior, and local SQLite is not tamper-proof.

## Two-minute setup

Requirements: Python 3.11+, Git. No third-party Python runtime dependencies.

```sh
git clone https://github.com/faysalishere/RepoContinuity.git
cd RepoContinuity
python -m pip install -e .
repocontinuity doctor
repocontinuity init
repocontinuity checkpoint capture
```

To use this in another Git repository, run `repocontinuity init` in that project's root. Initialization writes only its own private SQLite state. The state is excluded from Git tracking.

## Decisions and tasks

```sh
repocontinuity decision add --title "Keep current architecture" --rationale "No approved rewrite"
repocontinuity decision list
repocontinuity decision approve --id DECISION_ID --by "Project owner"
repocontinuity task add --title "Add regression tests"
repocontinuity task status --id TASK_ID --status complete_unverified
```

Each command prints JSON. Copy the returned IDs before using them. Approved decisions are immutable through the CLI; removals are soft deletes with `--confirm` and remain accessible through `list --all`.

## Explicit testing and verification

```sh
# Review this command. It runs with your current user's permissions.
repocontinuity evidence run --task-id TASK_ID -- python -m unittest discover -s tests
repocontinuity task verify --id TASK_ID --evidence-id EVIDENCE_ID
repocontinuity checkpoint list
```

`evidence run` executes the exact command you pass after `--`, with a timeout. It discards stdout/stderr and records the exit result, SHA/dirty status and an argument digest (not the command text). Do not run untrusted code or put secrets in command arguments. `evidence record` can record manual/review notes but **cannot** independently verify a task. A stale commit or dirty worktree blocks verification.

## Migrate from Phase 1 schema v1

```sh
repocontinuity doctor
repocontinuity migrate
repocontinuity doctor
```

`init` never upgrades existing databases silently. `migrate` creates a non-overwriting `state.sqlite3.v1.bak` in the private state directory before modifying the DB, preserving original data. Legacy, unsubstantiated `verified` flags are downgraded to unverified in v2 while the originals remain in the backup. For any migration error, keep the backup and inspect the issue; don't delete it.

## CLI reference

| Area | Explicit subcommands |
|---|---|
| Core | `doctor`, `init`, `migrate` |
| Decision memory | `decision add/list/update/approve/reject/remove` |
| Task memory | `task add/list/update/status/verify/remove` |
| Test/review evidence | `evidence record/run/list` |
| Git progress | `checkpoint capture/list` |

Run `repocontinuity <group> <subcommand> --help` for usage. The JSON handoff format is **a design only** in Phase 2; `export`, `import`, integrations and Agent Skills are reserved for Phase 3.

## Technical documents

[Architecture](docs/ARCHITECTURE.md) · [Schema v2](docs/DATA_CONTRACT.md) · [Draft JSON handoff](docs/HANDOFF_JSON_DESIGN.md) · [Security](docs/SECURITY_MODEL.md) · [Competition](docs/COMPETITORS.md) · [Roadmap](docs/ROADMAP.md)

## Testing and limitations

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
```

CI checks Python 3.11, 3.12 and 3.13 on Ubuntu, macOS and Windows. Check [GitHub Actions](https://github.com/faysalishere/RepoContinuity/actions) for the **current commit's** result; do not assume a previously green run validates later changes. This is pre-alpha, not a compliance tool or production security guarantee.

MIT licensed. Read [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md) before contributing.
