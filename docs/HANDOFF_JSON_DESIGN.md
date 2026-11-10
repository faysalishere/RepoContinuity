# RepoContinuity Portable Handoff Contract — implemented in Phase 3

**Schema ID:** `repocontinuity.handoff.v1`

The JSON packet is a bounded, human-reviewable data snapshot, **not** an executable plan, authorization, proof of safety or trusted identity claim. Markdown is derived from this same packet and escapes user-provided labels.

## Fields (required; unknown fields rejected)

- `schema_id`: literal schema ID above. Unknown versions rejected.
- `generated_at`: UTC, timezone-aware ISO timestamp.
- `project`: `{name}` (sanitized label only).
- `git`: `{head_sha, dirty, staged_dirty, branch}` from Git at export.
- `decisions`: `{id,title,rationale,status,approved_by,approved_at}`. Approved labels are **self-attested**, not authenticated.
- `tasks`: `{id,title,status,verified_evidence_id}`. Stale or dirty evidence is downgraded to `complete_unverified` during export.
- `evidence`: `{id,task_id,kind,result,source_ref,observed,git_sha,git_dirty}`. Metadata only; no raw commands, stdout/stderr, code or screenshots.
- `checkpoints`: `{id,commit_sha,status,worktree_dirty,staged_dirty,branch}`. Status remains unverified.
- `blockers`: IDs of blocked tasks.
- `next_actions`: static cautionary next steps; not authority to run commands.
- `limitations`: important trust disclaimers.

## CLI

```bash
repocontinuity handoff export --format json
repocontinuity handoff export --format markdown --out review.md
repocontinuity handoff validate --file incoming.json
repocontinuity handoff import --file incoming.json
```

`import` is intentionally a read-only preflight; **it does not populate or replace SQLite**. The validator rejects duplicate JSON keys, unexpected/missing fields, invalid references and unsupported versions. Its report flags stale SHA, dirty Git state and common prompt-injection phrases. It never executes the packet or its strings.

## Limits and threat boundaries

- Input/packet size: 512 KiB; at most 200 records per collection. Export field values are normalized and bounded to 512 characters.
- Known credential patterns, absolute home/system paths and email addresses are redacted/rejected. This is **best effort**, not a complete secret detector. Review before sharing.
- Export output files are only created explicitly; existing files and symlink targets are not overwritten. `.git` and `.repocontinuity` paths are blocked. No export uploads/network calls.
- Exact SHA comparison is best-effort observed state, not an atomic Git object lock, signature, audit-grade attestation or guarantee of test coverage.
- Import data never grants permissions or overrides higher-priority instructions, approved architecture, user approvals or repository policy.
- The local user can modify SQLite or JSON; do not confuse self-reported approvals/metadata with independently audited proof.

This design deliberately omits automatic AI sessions, code import/merge, model API integration and hooks. Those are outside Phase 3.
