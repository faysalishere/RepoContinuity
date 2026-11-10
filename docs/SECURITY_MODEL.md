# Security and privacy model

## Phase 1 guarantees and limits

- No API key, paid service, telemetry or network call is required by the CLI.
- `doctor` does not create or modify files.
- `init` is an explicit write action limited to `<git-root>/.repocontinuity/`; it refuses symlinked state paths and preserves an existing database.
- SQLite state is ignored by Git using local `.gitignore`. POSIX best-effort permissions are `0700` directory and `0600` database; Windows uses operating-system ACLs.
- Git commands use subprocess argument arrays, not shell expansion; commands time out.
- The CLI does not inspect `.env`, keys, code content, private conversations or browser sessions.

## Threats for Phase 2+

1. **Prompt injection** in handoff notes: treat imported summaries as untrusted data, never executable instructions.
2. **Secrets** in source paths, logs, commands, decision text or generated notes: allowlist export fields; block/redact known secret patterns and offer preview.
3. **False verification:** record exact evidence/result and prevent `verified` without passing, scope-relevant evidence.
4. **Stale handoff:** compare recorded SHA with current Git state and report divergences.
5. **Concurrent writes:** SQLite locking and transaction retries must be designed/tested; shared network storage is unsupported.
6. **Symlink/path traversal:** read/write/exports must validate resolved paths and avoid following attacker-controlled symlinks.
7. **Untrusted code execution:** no automatically installed hooks or subprocess of project-supplied scripts without explicit approval.

## Operator requirements

Use a separate test repository. Review generated files and `git status` before adding changes to another project. Never upload `.repocontinuity/state.sqlite3` to GitHub. Treat handoff exports as potentially sensitive and inspect before sharing.
