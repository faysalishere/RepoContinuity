# RepoContinuity — 2-minute Quick Start (v0.4.0 beta)

**Free; Python 3.11+ and Git required.** No API key, cloud account, service, or third-party runtime dependencies. GitHub Desktop alone does not always expose `git` in `PATH`.

## Option A: Test safely without touching a real project

```sh
git clone https://github.com/faysalishere/RepoContinuity.git
cd RepoContinuity
python -m pip install .
python examples/quickstart_demo.py
```

The interactive 4-step walkthrough creates and deletes **its own temporary Git repository**. It demonstrates SQLite init, proposed/approved decision, a completed-but-unverified task, a Git checkpoint, versioned JSON handoff and validation-only import. Run `python examples/quickstart_demo.py --yes` to skip prompts for CI. No network calls are performed by the demo itself.

If you cannot install Python packages, run the demo from a source checkout using `PYTHONPATH=src python examples/quickstart_demo.py --yes` (on Windows CMD: `set PYTHONPATH=src && python examples/quickstart_demo.py --yes`). The sample Git repository always remains temporary.

**Expected final output:** `DEMO COMPLETE` and `Task remains UNVERIFIED`.

## Option B: Try on your own Git repository

Back up your project first, review `git status`, then run:

```sh
repocontinuity doctor
repocontinuity init
repocontinuity decision add --title "Do not rewrite the approved architecture"
repocontinuity task add --title "Run real regression tests"
repocontinuity handoff export --format markdown
```

The `init` command writes only to a `.repocontinuity` directory; the `handoff export` to stdout is read-only. Never commit the SQLite state, passwords, or unreviewed handoff output. Do not run `evidence run` with commands you do not trust: it executes the specified command under your local account.

## Understand the safety boundary

`verified` represents a passing, tool-observed command on the same clean Git commit—not general security or correctness assurance. Imported JSON never applies changes, authenticates approvals, or installs skills. Handoff output can contain user-provided sensitive information despite best-effort redaction; **review before sharing**.

Want the full workflow? See [README](../README.md), [cross-agent usage](CROSS_AGENT_USAGE.md), and [security](SECURITY_MODEL.md).
