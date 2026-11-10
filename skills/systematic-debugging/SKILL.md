---
name: systematic-debugging
description: Find and verify the root cause of a software failure before applying a minimal repair. Use for bugs, regressions, broken CI or unexpected CLI behavior.
license: MIT
---

# Systematic debugging

1. Collect a minimal reproducible error, environment, version, exact failing command and relevant logs. Redact secrets before sharing.
2. Separate observed facts from guesses. Confirm baseline behavior and identify the last known working state when available.
3. Trace the failing path through relevant code, configuration, dependencies, environment and data flow.
4. Construct one clear root-cause hypothesis, and attempt a falsifying test rather than random edits.
5. Apply the smallest verified repair. Add a regression test that failed before and passes after the fix when feasible.
6. Test across supported environments when behavior is platform-dependent. Preserve failure evidence and record remaining uncertainty.
7. If reproducibility or source access is missing, mark the diagnosis provisional and stop before destructive changes.

**Output:** symptoms, cause and supporting evidence, changed files, precise tests, remaining risks.
