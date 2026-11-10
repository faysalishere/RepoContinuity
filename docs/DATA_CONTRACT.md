# Initial data contract (schema v1)

The Phase 1 SQLite schema is a persistence foundation, not a public API. Fields are provisional until Phase 2.

| Table | Purpose | Validation policy |
|---|---|---|
| `projects` | One entry per initialized repository | UUID, name, UTC timestamp |
| `decisions` | Proposed/approved/rejected architecture or scope decisions | approved entries must have approver and approval timestamp |
| `tasks` | Explicit work items | planned, in_progress, blocked, complete_unverified, verified |
| `evidence` | Task-linked review/test/manual evidence reference | result pass/fail/unknown; foreign key must exist |
| `checkpoints` | Commit-linked progress snapshots | unverified/verified |
| `schema_meta` | Migration compatibility | version 1 |

**Important:** SQL constraints alone do not prove tests ran. Enforcing evidence-backed status transitions and signed/traceable approval is a Phase 2 requirement. Phase 1 does not expose arbitrary writes or permit marking anything verified through the CLI.

Future JSON exports should contain `schema_version`, `project`, `git`, `decisions`, `tasks`, `evidence`, `pending`, and `generated_at`, and never silently include absolute local paths, credentials or hidden source files. Exact JSON schema will be approved before Phase 3.
