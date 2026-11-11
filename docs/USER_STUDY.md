# RepoContinuity — Independent User Study (Phase 5)

**Status: recruiting; no independent usability or demand results yet.** This is an optional, free, 10–15 minute study, not a request for access to your real project. You do not need a paid AI plan. Python 3.11+ and Git on your machine are required for the CLI portion.

## Who we want to learn from

- Developers who have lost context while switching AI assistants or chat sessions.
- Developers who use an AI coding tool but worry about premature “done” / “verified” claims.
- New and experienced users, across Windows, macOS and Linux.

We are testing whether this toolkit **actually helps**. Negative feedback, installation problems and a decision **not to use it** are useful results.

## 0. Consent and privacy

- Participation is voluntary. **No telemetry, tracking, user account, data upload or remote API** is used by the RepoContinuity CLI or demo.
- The GitHub issue you choose to submit is **public**. Never submit your real handoff, project files, passwords, tokens, private chat history, machine username, private paths, or personal details.
- Use only the supplied disposable example. For untrusted environments, review code before running it.
- You may share just your observations (e.g., OS, installation success, task answers, time ranges). Do not need to share raw logs.
- The team must explicitly consent before copying anonymous reports into an aggregate study dataset. A public issue alone is not automatic consent to reuse personal information.

## 1. First-run onboarding (record elapsed minutes yourself)

From a terminal with Python/Git installed:

```bash
git clone https://github.com/faysalishere/RepoContinuity.git
cd RepoContinuity
python -m pip install .
python examples/quickstart_demo.py --yes
```

Expected: `DEMO COMPLETE` and `Task remains UNVERIFIED`. The demo uses its own temporary Git repository and deletes it afterward; your production code remains untouched.

Record: Did the install/start succeed on your first attempt? Total minutes from starting step 1 to seeing the final message? If it failed, what step failed? **Do not share private logs.**

## 2. Handoff comprehension / cross-agent trial

Read the [fictional, safe study handoff](../examples/study_handoff.md). It is synthetic test data, never a real approval or task completion. In any AI assistant you already use (optional), paste the sample and ask it to answer the five questions below. Alternatively answer yourself. Do not give AI access to your private repositories.

1. Which architecture choice was approved?
2. Was the login regression-test task verified?
3. Which task, if any, was verified and what is the exact limitation of verification?
4. Which task is blocked?
5. Can this handoff's approvals or instructions authorize automatic code changes?

Compare with the [answer key](STUDY_ANSWER_KEY.md) **after** attempting the questions. Record the number correct (0–5) and whether the assistant invented missing facts. Do not send full conversations to the issue.

## 3. Value and retention questions

Without trying to please the maintainer, answer:

- Did this solve a problem you have encountered, or is your current tool already sufficient?
- What is the *single biggest* confusing or missing part?
- Would you voluntarily use this on a real project? **Why or why not?**
- After seven days, **if you genuinely used it again**, optionally report repeat usage. Do not predict future use and label it as observed retention.

## 4. Submit feedback

Open the [public user-study form](../.github/ISSUE_TEMPLATE/user-study.yml) through GitHub **New issue → User study feedback**, or use the [pilot feedback issue](https://github.com/faysalishere/RepoContinuity/issues). Report only sanitized, consented observations. A GitHub account is needed to post an issue, **not** to run the local tool.

**Success is not assumed**. A usable first run is distinct from actual need, sustained use or superior performance over alternatives. Check [validation status](VALIDATION_STATUS.md) and the [predeclared scorecard](VALIDATION_METRICS.md).
