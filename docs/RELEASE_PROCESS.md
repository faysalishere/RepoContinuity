# Phase 4 Public Beta — release process

**Target version: `0.4.0b1` (Git tag `v0.4.0b1`).** A public beta is not a stable 1.0. Naming collision checks in GitHub are not trademark or PyPI clearance. **Do not publish to PyPI without a separate explicit authorization and namespace check.**

## Local checks (no network required if build requirements are installed)

```sh
PYTHONPATH=src python -m unittest discover -s tests -q
PYTHONPATH=src python examples/quickstart_demo.py --yes
python scripts/check_release.py
python -m pip wheel . --no-deps --no-build-isolation --wheel-dir dist
```

Verify a fresh virtualenv install from `dist/` and run `python -m repocontinuity --version`, `python examples/quickstart_demo.py --yes`. Wheel metadata must match the version. Git working tree must be clean. Run full GitHub Actions matrix before tagging.

## GitHub Release workflow

`.github/workflows/release.yml` builds a wheel + source distribution on an **explicit `v*` Git tag** and attaches them to a GitHub pre-release. It is not triggered by ordinary pushes. The workflow verifies the tag equals the version in `pyproject.toml`, runs tests and quick start, packages files, and generates SHA-256 checksums. The release uses GitHub's ephemeral `GITHUB_TOKEN` with `contents: write` only for its publishing job.

After all checks pass, the owner can create/push `v0.4.0b1` from the verified commit. Alternatively, on GitHub mobile/web open **Releases → Draft a new release**, create a new tag named `v0.4.0b1` from the verified `main` commit, select **This is a pre-release**, and publish. The tag push triggers the packaging workflow; if the prerelease already exists, the workflow attaches any missing assets without overwriting existing ones. **Do not move an existing release tag.** Review the [release notes](../RELEASE_NOTES.md) before publishing.

## Public support and limits

- Supports Python 3.11–3.13 on Windows, macOS, Linux, subject to current CI results.
- Requires Git on `PATH`; all CLI features remain local and opt-in.
- No private repo or chat data is uploaded by the tool.
- The five skills are plain documents, not native marketplace plugins.
- Manual `handoff import` is a validation alias; it does not restore databases or sessions.

For Phase 5, collect reports about first-run success, incorrect verification, handoff fidelity and repeated use. Do not run user-data collection automatically.
