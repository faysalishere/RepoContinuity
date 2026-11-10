# RepoContinuity

**Approval-aware, evidence-verified handoff for AI-assisted software development.**

> **Status: Phase 1 foundation / pre-alpha. Not yet an AI memory agent, plugin, or working cross-agent handoff engine.**

RepoContinuity aims to preserve what an AI-assisted project actually **approved, changed, tested, and left unfinished**, without pretending that a generated summary is evidence of correctness. A future export will be portable between coding assistants.

## Why another continuity tool?

Several mature open-source/hosted tools already implement agent memory and handoff. RepoContinuity focuses narrowly on **human approval boundaries and explicit verification evidence**. `unverified` will never be treated as `verified` merely because an assistant says a task is done. This distinction is a design goal, not a feature claim for Phase 1.

## Try the Phase 1 foundation

Requirements: Python 3.11+ and Git. No API key, server, external Python dependency or AI subscription.

```sh
git clone https://github.com/faysalishere/RepoContinuity.git
cd RepoContinuity
python -m pip install -e .
repocontinuity --version
repocontinuity doctor
repocontinuity init
repocontinuity doctor
```

If GitHub publishing is not complete, use the source ZIP and replace the clone step with extracting it and entering the project folder. The package can also be used without installation with `PYTHONPATH=src python -m repocontinuity doctor`.

`doctor` prints read-only JSON diagnostics. `init` explicitly creates `.repocontinuity/state.sqlite3` in the Git repository root. This local state directory is excluded by the provided `.gitignore` and has a nested ignore policy if used in other repositories. Existing initialized state is preserved; there is no background capture or network request.

## Architecture

- **CLI:** Python standard library, explicit commands only.
- **Persistence:** local SQLite (`schema_version=1`), foreign keys and constrained statuses.
- **Version provenance:** read-only Git repository discovery; Git commit checkpoint capture is deferred to Phase 2.
- **Sharing:** future opt-in Markdown/JSON exports; never export SQLite private state by default.
- **Safety:** no source-code writes, network calls, hooks, automatic watchers, or secret collection.

See [architecture](docs/ARCHITECTURE.md), [data contract](docs/DATA_CONTRACT.md), [security boundaries](docs/SECURITY_MODEL.md), [market review](docs/COMPETITORS.md), and [roadmap](docs/ROADMAP.md).

## Test

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
```

CI is configured for Python 3.11-3.13 on Ubuntu, macOS and Windows. The hosted CI result must be checked separately after publication. Tests cover foundation invariants only; they do not demonstrate Phase 2+ functionality.

## Current limitations

- No decision/task recording commands, verification engine, handoff exporter, or integrations yet.
- No automatic discovery of existing AI sessions.
- An existing `state.sqlite3` is version-checked, but upgrades and corruption recovery are not yet available.
- Name/package/trademark availability must be verified before general-release branding.

**License:** MIT. Contributions and design reviews welcome once the API contract is stabilized.
