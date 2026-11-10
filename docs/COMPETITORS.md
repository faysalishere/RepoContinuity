# Competitive and naming audit — 2026-11-10

## Name check

- `faysalishere/RepoContinuity` was not found when queried through the GitHub connector.
- GitHub repository search returned no exact repository named `RepoContinuity`/`repocontinuity`, but did return `repo-continuity` repositories owned by others (e.g., `vector233/repo-continuity`).
- Search absence is **not** trademark, domain, npm, or PyPI clearance. Do not make uniqueness claims or publish to package registries until separately verified.

## Direct/adjacent competitors

| Competitor | What exists | Positioning risk for us |
|---|---|---|
| ECC — https://github.com/affaan-m/ECC | broad agent harness, workflows, skills, hooks and memory | our product cannot just repackage skills |
| AgentMemory — https://www.agent-memory.dev/ | agent memory and cross-agent handoff | cross-agent memory alone is not unique |
| Codemem — https://codemem.sh/ | local-first agent coding memory | local-first alone is not unique |
| Continuity — https://www.getcontinuity.io/docs | decision governance, Git-backed memory, session handoff | very close overlap on decisions and provenance |
| Reinstate — https://reinstate.dev/about/reinstate | session transfer and structured cross-agent handoff | handoff alone is not unique |
| RepoPact — https://github.com/JeremyShows/repopact | repo-native authority, evidence, audits and project state | **strong overlap**; any differentiation requires testing against its workflow |

## Positioning hypothesis (requires validation)

Build the small missing reliability layer rather than competing on the largest memory index:

- distinguish **proposed** from **human-approved** decisions;
- distinguish **code written** from **test-backed verified** completion;
- preserve the exact state used for each claim, including untested changes;
- produce a short, portable handoff with a list of non-authorized next steps.

**No market demand is proven by competitor existence.** Phase 5 must seek repeated use and evidence that this workflow offers value over existing tools.

Sources checked: official docs/README for ECC, AgentMemory, Codemem, Continuity Reinstate and RepoPact plus GitHub repository search. Product descriptions may evolve.
