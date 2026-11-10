# Contributing

RepoContinuity is pre-alpha. Please open an issue proposing changes before adding features or changing the approved phase scope.

1. Keep contributions within the currently approved phase; avoid automated watchers, remote APIs or agent integrations in Phase 1.
2. Preserve backwards compatibility for existing schema v1 and CLI commands.
3. Add standard-library tests for bug fixes and changed behavior.
4. Never commit `.repocontinuity/`, credentials, `.env`, real conversations or unredacted project data.
5. Distinguish `implemented`, `tested`, `verified`, and `not yet supported` in documentation.

Run tests with `PYTHONPATH=src python -m unittest discover -s tests -v`. Security reports: see `SECURITY.md`.
