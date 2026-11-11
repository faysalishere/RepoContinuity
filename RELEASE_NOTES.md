# RepoContinuity v0.4.0b1 — Public Beta Candidate

Local-first, evidence-aware project memory for developers using AI coding assistants.

## Included

- Decision and task lifecycle with explicit, user-attested approvals.
- Git SHA checkpoints and observed command evidence with conservative `verified` rules.
- SQLite schema v2 and backed-up schema v1 migration.
- Portable versioned JSON/Markdown project handoffs, read-only validation-only import.
- Five reusable model-agnostic Agent Skills.
- **New:** interactive, disposable 2-minute CLI walkthrough; release smoke checks, end-to-end tests and improved JSON/file safety.

## Not included

- Automatic reading of chats, native Claude/Codex/Cursor plugins, session syncing, cross-device database merge, authenticated approver identities, code correctness guarantees.

## Install

Requires Python 3.11+ and Git. Download the source archive from the GitHub release and `python -m pip install .` from its extracted directory, or install the attached wheel via `python -m pip install path/to/repocontinuity-0.4.0b1-py3-none-any.whl`. No API key needed.

See [2-minute quick start](docs/QUICK_START.md), [security audit](docs/SECURITY_AUDIT.md) and [release process](docs/RELEASE_PROCESS.md). Always inspect handoff contents for sensitive data before publication.
