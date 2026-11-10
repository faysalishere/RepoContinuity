# Security model — Phase 2

## Local trust boundary

- No paid API, telemetry, cloud calls, auto-sync, AI prompts or background recording.
- Only explicit commands write to private SQLite. `doctor` remains read-only.
- `init`/`migrate` refuse symlinked state directories/databases. Migration creates a SQLite-consistent v1 backup without overwrite. `migrate` never runs automatically.
- `.repocontinuity` is ignored by Git. POSIX best-effort permissions are state directory `0700` and database/backup `0600`; Windows uses OS permissions.
- Git metadata uses a subprocess argument array, no shell, timeout, and avoids file-name storage.

## Test execution — important

`evidence run --task-id ID -- COMMAND ARG...` **executes the specified program** with the current user's privileges. It could modify files or invoke the network, depending on the program. This action is opt-in and must only be used with reviewed, trusted test commands. The tool never runs a command on its own. It suppresses output and records only exit result, Git provenance, and an argument digest. Exit status 0 is limited evidence, not proof of functional correctness, security or coverage. Commands may still access secrets on the host; run untrusted projects only in a sandbox.

Manual evidence `record` can never verify a task by itself. DB triggers guard accidental direct updates, but an operator controlling the SQLite file may intentionally alter records; this is not tamper-evident or a substitute for signed attestations.

## Current limitations and future threats

- Prompt injection in eventual imported handoffs remains a Phase 3 concern; never execute untrusted notes.
- Secrets may be present in manually entered decision titles/notes. No claim of database-wide automatic redaction.
- Concurrent writes from many processes and shared network filesystems are unsupported. SQLite is meant for local, low-write workflows.
- Files can change between Git observations; this is a best-effort snapshot, not an atomic source tree lock.
- Long-running or malicious commands might leave child processes; explicit user choice does not make an untrusted command safe.
- JSON export/import is NOT implemented yet. Phase 3 must include redaction, validation and bounded output.

Never commit `.repocontinuity/`, `.env` or credentials. Review repository status before running Git operations. Keep CreativeCode Engine and unrelated projects untouched.
