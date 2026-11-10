# SQLite schema v2 (Phase 2)

The SQLite database is local operational state, not a cross-model export format.

| Table | Important fields | Semantics |
|---|---|---|
| `schema_meta` | `version=2` | v1 migration requires explicit command and backup |
| `projects` | ID, name, created timestamp | Project initialized under Git root |
| `decisions` | title, rationale, proposed/approved/rejected, approved_by, approved_at, deleted_at | Explicit approval, no editing of approved decisions |
| `tasks` | planned/in_progress/blocked/complete_unverified/verified, `verified_evidence_id`, deleted_at | Verified requires observed passing test evidence |
| `evidence` | task_id, kind, result, source_ref, `observed`, `git_sha`, `git_dirty` | Observed=1 only for actual tool-launched command |
| `checkpoints` | git SHA, branch, staged/dirty flags, status | Capture defaults to unverified; only real Git commits |
| `activity_log` | entity ID, action, timestamp | Metadata-only append log (not a tamper-proof audit log) |

The database enforces foreign keys, status checks, immutable evidence records and a trigger preventing an unsupported `verified` task status. `verified` checkpoints are rejected. The CLI also validates Git cleanliness and the exact commit SHA.

**Caution:** manually supplied decision text, evidence URLs and approver labels may contain sensitive material. No automatic redaction of the private SQLite database is promised. Review values before recording; never commit or share `.repocontinuity/`.

V1 columns remain and legacy records are retained across migration, apart from *status downgrades* for unsubstantiated legacy `verified` entries. A protected SQLite backup preserves original data.

The [handoff JSON contract](HANDOFF_JSON_DESIGN.md) is a proposal for Phase 3. No export or import capability is implemented in this phase.
