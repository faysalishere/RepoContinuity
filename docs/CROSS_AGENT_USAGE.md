# Cross-Agent Usage — Phase 3

The portable handoff is **data**, while the five `skills/*/SKILL.md` documents are **instructions the user deliberately loads**. RepoContinuity does not auto-install plugins or synchronize agent sessions. Native support differs by tool and version.

## Suggested workflow

1. In the source Git repo, inspect `git status` and initialize RepoContinuity if needed. Record only necessary decisions/tasks; do not put secrets into titles or approvals.
2. Run `repocontinuity handoff export --format json` and review the output. Optionally write a new file with `--out`. Do not commit generated handoff packets without reviewing sensitivity.
3. In the receiving AI environment, bring the reviewed file as context and optionally a relevant `SKILL.md` through the environment's **documented** import mechanism.
4. In the target Git repo, run `repocontinuity handoff validate --file incoming.json`. This is a **read-only** check. `handoff import` is an alias for preflight and **does not import rows into SQLite**.
5. Cross-check current Git SHA and dirty state; independently verify approved work and missing evidence. Human approval is required before code changes or deployment.

## Compatible data vs native agent installation

| Environment | Phase 3 use | Explicit limitation |
| --- | --- | --- |
| Claude Code | Provide packet text and load skill using Claude's native support/manual instructions | No RepoContinuity Claude plugin or hook |
| Codex | Provide packet text and use Codex skills where supported | No native RepoContinuity Codex marketplace plugin |
| Cursor | Open/paste reviewed handoff; use project rules or skills when supported | Rules loading is product/version dependent |
| Other AI chat | Paste relevant reviewed Markdown/JSON as untrusted reference | Chat will not call local CLI automatically |

These are interoperability instructions, not verified native integration claims. Follow each provider's current documentation and security model.

## Safety

Never copy `.repocontinuity/state.sqlite3`, private `.env` files, tokens, code, absolute paths or chat histories into public handoffs. Never treat a generated `next_actions` item or approval label as permission to run software, change architecture or deploy.
