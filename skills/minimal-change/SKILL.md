---
name: minimal-change
description: Apply the smallest safe code change while preserving existing behavior and decisions. Use when fixing defects or implementing an approved change in an existing project.
license: MIT
---

# Minimal-change implementation

**Prerequisite:** an approved, bounded task and a current understanding of the repository.

1. Capture `git status` and HEAD. Identify unrelated uncommitted edits; preserve them.
2. Inspect relevant source files and tests; never add duplicate implementations or new frameworks where a current module can be fixed.
3. Define an observable acceptance test and execute it if safe. Distinguish a reproduction from an assumption.
4. Change only the necessary paths. Keep existing architecture, public interfaces, versions and dependencies unless approval explicitly allows otherwise.
5. Run targeted tests, then relevant regressions. Inspect the diff for changed permissions, new network calls, secret exposure and inadvertent deletions.
6. When unexpected behavior occurs, stop and report the blocker; never silently force push or rewrite unrelated code.
7. Report which files changed, the tests actually run, test outcomes and any unverified risks.

**Do not** treat a successful build as proof of functional or security correctness. Never deploy without explicit release authorization.
