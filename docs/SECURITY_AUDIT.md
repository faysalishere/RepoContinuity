# Phase 4 Security Audit — 2026-11-11

Scope: source inspection, explicit handoff validation hardening and temporary-repository tests. **This is an internal review, not a third-party penetration test.**

| Area | Mitigation / test | Residual limitation |
| --- | --- | --- |
| Untrusted handoffs | Strict JSON schema, duplicate-key rejection, 512 KiB bounded reads, non-finite numeric rejection | Natural-language prompt injection cannot be perfectly detected |
| Untrusted approvals | Imports always require human review and never write state | Approval labels remain user-asserted; no authentication |
| Secrets | Allowlisted export fields, common-token/path redaction | Novel secrets or personal information may evade patterns; review before sharing |
| SQLite | Local state, versioned schema, FK/status triggers, explicit backed-up migration | Local database is not tamper-proof; OS filesystem access matters |
| Writing exports | Exclusive new-file creation, path policy, rejects user-controlled symlink ancestors (OS-managed root aliases like macOS /var are allowed) | Races from other privileged local processes are out of scope |
| Git provenance | Real commit SHA and dirty/staged flags; stale verification downgraded | Tests may be incomplete or unrepresentative |
| Command execution | `evidence run` requires explicit user-supplied argv, finite timeout, no shell interpolation | Arbitrary explicitly chosen commands run with the user's own privileges |
| Network and telemetry | No runtime network calls by CLI, demo, or validators | Installing/building via pip can contact index unless offline flags/caches used |
| CI and supply chain | Limited token permissions for tests, minimal third-party actions, project version/skills checks | GitHub-hosted runners/actions remain a third-party trust boundary |

## Release go/no-go gates

1. 100% unit/integration tests passing on supported Python versions and operating systems.
2. Wheel build and installation smoke test pass; no undeclared runtime dependencies.
3. Offline release checks pass; no private DB or `.env` packaged.
4. Manual audit of published release notes and install instructions.
5. Mark any missing evidence or deployment limitation explicitly. Do not claim compliance certification.

The tool has **no automated session ingestion** and the `handoff import` command is **validation-only**, not a merge operation. These limits must remain visible to users in the public release.
