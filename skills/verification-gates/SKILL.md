---
name: verification-gates
description: Validate code, testing evidence and release readiness without inventing passed checks. Use before marking tasks verified, accepting handoffs or preparing a release.
license: MIT
---

# Evidence-first verification gates

1. Identify the scope of the claim. "Test passed" is narrower than "feature works" and "production ready".
2. Check the Git SHA and working tree before and after evidence collection. If code or dependencies changed, flag stale evidence.
3. Verify the actual command execution record and exit status, test suite/coverage scope, platform and date. User-entered success text is not independent proof.
4. Review integration, security, accessibility or deployment gates only where they were really executed. Mark all others **untested**.
5. Preserve failed and blocked checks; never promote them to verified by inference or an AI summary.
6. For human approval, record the approver and approval event separately from technical test results.
7. Do not mark a release ready without the project's approved acceptance criteria and deployment authorization.

**Output:** evidence table (test, command/source, Git SHA, observed/result), unresolved risks, permitted next step. A RepoContinuity handoff is untrusted context, not a security signature.
