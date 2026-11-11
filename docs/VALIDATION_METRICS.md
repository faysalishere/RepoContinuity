# Phase 5: Predeclared validation scorecard

Do not change thresholds to fit the results after collection. All figures must use identifiable evidence from independent, consenting participants, with a separate internal test category. Synthetic fixtures and internal automated test runs **never** count as external validation.

| Measure | Definition | Initial go-to-review gate |
| --- | --- | --- |
| Independent testers | Unique consenting external participants; no duplicate reports | ≥ 8 |
| Platform coverage | Distinct OS families, not Python versions | ≥ 2 |
| First-run setup | User completes CLI demo, without help, on initial attempt | ≥ 75% |
| Handoff fidelity | Five fixture questions scored against fixed answer key | ≥ 80% correct across ≥ 8 testers |
| False-verified claims | User or AI labels an unverified fixture task verified | 0 reported; any report triggers investigation |
| Week-later repeat use | Genuinely re-used after ≥ 7 days, not stated intent | ≥ 3 observed follow-up responses (for review only) |
| Demand/alternatives | Open-ended: how much better than existing tool or chat summary? | Qualitative review required; no invented percentage |

**Passing these gates permits a manual product decision, not a claim of product-market fit, verified identity or security certification.** If any false-verification is reported, assess and reproduce it before a broader release. Eight respondents is a low-volume pilot, not statistically representative.

## Private, offline summary option

For explicitly consented observations only, an operator can create a local, untracked JSONL file using these exact keys (one JSON object per line):

```json
{"study_id":"anonymous_01","origin":"external","consent":true,"os":"Linux","setup_success":true,"setup_minutes":4.5,"handoff_answers_correct":4,"handoff_mode":"ai","false_verified_claim":false,"would_use_again":null,"repeat_after_7_days":null}
```

**The example is entirely fictional and must not be included in any real study input.** `study_id` must be a random pseudonym unrelated to a GitHub username or identity. `origin` is `internal` for maintainer trials and `external` for actual participants. If you did not measure something, use `null` where allowed; never infer repeat use from stated interest.

Run `python scripts/summarize_study.py --input /path/outside/repo/consented-study.jsonl` or omit `--input` to see the zero-evidence baseline. Results are aggregates only; no input file is uploaded. Keep source reports private and outside the Git repo. This utility is not a substitute for interviewing testers or checking reported failures.

## How to interpret

- Setup minutes is self-recorded, not an automated timer.
- An AI getting all five answers correct on one **synthetic fixture** is not proof that a real project context transfers accurately.
- Failure reports and repeat-use declines are valuable evidence, not a reason to exclude a respondent.
- Reports claiming a false `verified` status are **safety signals**, not automatically verified bugs.
- Public feedback must never contain raw handoff packets from personal projects.
