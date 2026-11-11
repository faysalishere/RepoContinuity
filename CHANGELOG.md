# Changelog

## Unreleased — Phase 5 independent-user validation setup (2026-11-11)

- Added opt-in user study guide, synthetic handoff and fixed comprehension answer key.
- Added voluntary GitHub feedback issue form and privacy warnings.
- Added an offline, consent-gated study aggregator that excludes internal runs and rejects duplicate respondents.
- Predeclared validation thresholds; external participant results and seven-day repeat usage are **not yet observed**.
- No changes to the existing CLI, SQLite schema, paid services or automatic telemetry.


## 0.4.0b1 — Phase 4 public beta prerelease (2026-11-11)

- Interactive, isolated 2-minute demo with no writes to user projects.
- Safer untrusted JSON parsing (bounded read, no NaN/Infinity), review-by-default import preflight and symlink ancestor checks.
- Added integration/security regression tests, release preflight validator and reproducible wheel smoke workflow.
- Documented public release process, security limits, packaging and handoff examples.
- Official [`v0.4.0b1` GitHub prerelease](https://github.com/faysalishere/RepoContinuity/releases/tag/v0.4.0b1) published with wheel, source distribution and SHA256 checksum assets; independent user validation remains pending.

## 0.1.0a1 — Phase 1 foundation (2026-11-10)

- Initialized a stand-alone repository structure for RepoContinuity.
- Added read-only `doctor` and explicit `init` commands.
- Added private local SQLite schema v1 for projects, decisions, tasks, evidence and checkpoints.
- Added safe Git root lookup, idempotent initialization and schema fail-closed behavior.
- Added isolated Python standard-library tests and cross-platform GitHub Actions CI configuration.
- Documented market overlap, security boundaries, roadmap and data contract.

**Historical note:** `v0.1.0a1` was not a separate GitHub Release. `v0.4.0b1` is a published GitHub prerelease; no PyPI publication is claimed.

## 0.2.0a1 — Phase 2: Memory & Checkpoints (2026-11-10)

- Added explicit decision and task create/list/update/soft-delete operations and human-attested approval.
- Added observed test evidence records and task verification linked to clean Git SHA.
- Added real Git checkpoint capture with staged/dirty flags, no source file names.
- Introduced SQLite v2 schema and explicit SQLite-native backed-up migration from v1.
- Added fail-closed guards for unverified legacy statuses and immutable evidence rows.
- Documented future portable JSON handoff format; **no handoff exporter or AI integration is shipped**.

## 0.3.0a1 — Phase 3: AI Handoff & Skills (2026-11-11)

- Added opt-in, bounded, allowlisted JSON/Markdown handoff export.
- Added strict schema validation, duplicate-key rejection, size limits and read-only `handoff import` preflight.
- Added Git SHA/dirty-state checks, stale verification downgrade on export and security warning markers.
- Added best-effort redaction, Markdown escaping and five portable Agent Skills.
- Kept SQLite schema v2 and earlier CLI operations unchanged.
- No automatic session capture, hooks, network sync or state merging.
