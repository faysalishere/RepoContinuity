# Approved roadmap — RepoContinuity

Phase changes require owner approval. CreativeCode Engine remains separate and unchanged.

- **Phase 1 — Foundation & Architecture: COMPLETE.** Competitor/name audit, Python CLI skeleton, SQLite schema v1, 9/9 cross-platform CI jobs.
- **Phase 2 — Memory & Checkpoints: COMPLETE.** Explicit decisions/tasks, human-attested approval, observed evidence, real Git checkpoints, protected v1→v2 migration. 9/9 CI jobs passed.
- **Phase 3 — AI Handoff & Skills: COMPLETE (9/9 GitHub Actions matrix jobs passed).** Versioned JSON/Markdown exports, safe read-only import validation, five portable Agent Skills, tests and docs.
- **Phase 4 — Public Release: COMPLETE (public beta).** The `v0.4.0b1` GitHub prerelease was published on 2026-11-11 with wheel, source distribution and checksums; 10/10 tag CI jobs and the release workflow passed. This is not a stable-production certification.
- **Phase 5 — Real User Validation: ACTIVE (recruiting; no external evidence yet).** Published opt-in study protocol, fixed answer key, feedback form and consent-gated local aggregate. Measure context loss, handoff correctness, setup success and actual repeat use; do not mark completed without independent participants.

## Phase 3 exit checklist

- [x] Inspect and preserve Phase 2 GitHub source and approved boundaries.
- [x] Export allowlisted, versioned JSON and human-reviewable Markdown on explicit request.
- [x] Reject invalid or oversized packets; import is validation-only and never writes project state.
- [x] Surface stale Git state, dirty trees and unverified evidence; avoid false verification.
- [x] Package five Agent Skills with standard YAML frontmatter and safe instructions.
- [x] Add local tests and model-agnostic usage documentation.
- [x] Verify GitHub Actions cross-platform matrix and remote readback after push.
- [x] Owner approval before Phase 4 (given on 2026-11-11).

## Phase 4 acceptance checklist

- [x] Phase 4 explicitly approved by owner.
- [x] Isolated quick start demo and public documentation implemented.
- [x] E2E regression tests and release safety checks added.
- [x] Initial internal security audit and package workflow documented.
- [x] GitHub Actions full compatibility matrix passed for the published `v0.4.0b1` tag (10/10 jobs).
- [x] Git tag and GitHub pre-release published with wheel, sdist and `SHA256SUMS.txt` assets (release workflow passed; checksum asset present).
- [x] Owner approval to begin Phase 5 (given on 2026-11-11).

## Phase 5 exit criteria (pending real users)

- [x] Owner approved Phase 5 on 2026-11-11; CreativeCode Engine remains unchanged.
- [x] Independent-user guide, safety notes, fixed synthetic handoff + answer key prepared.
- [x] Feedback submission path and consent-gated aggregate pipeline developed.
- [x] CI and hosted GitHub read-back for Phase 5 revision completed (10/10 jobs on `cd05c08f`).
- [ ] At least 8 independent consenting pilot reports and a documented review of failures.
- [ ] At least 3 genuine seven-day repeat-use follow-up responses.
- [ ] Owner review of go/no-go decision based on real observations.

See [Phase 5 scorecard](VALIDATION_METRICS.md) and [current status](VALIDATION_STATUS.md).
