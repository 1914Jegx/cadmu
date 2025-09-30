# Automation Overview

CADMU relies on several automation layers to keep quality high and contributions
smooth.

## Continuous Integration (GitHub Actions)

Workflow: [.github/workflows/ci.yml](../.github/workflows/ci.yml)

Steps executed on Ubuntu runners:
1. Check out repository
2. Set up Python 3.11
3. `pip install -e .[dev]`
4. `ruff check .`
5. `mypy src`
6. `pytest`

Failures in any step block merges. Extend this workflow when adding new tools
(e.g., coverage upload, documentation build).

## Future Automation Ideas

- **Dependabot**: Automatically open PRs for dependency updates (Python + Actions).
- **Codecov/Coveralls**: Upload coverage reports to track trends.
- **Release Drafter**: Generate release notes from merged PRs.
- **Security Scans**: Add workflows using `pip-audit` or GitHub’s CodeQL.
- **Nightly Diagnostics**: Cron job that runs `cadmu diag --compress` for long-term benchmarking.

## Local Automation

- `Makefile` target `qa` replicates the CI pipeline.
- `.pre-commit-config.yaml` can be installed locally to enforce linting, typing,
  and tests before commits.

## Issue & PR Templates

Located in `.github/` to standardise reports:
- `ISSUE_TEMPLATE/bug_report.md`
- `ISSUE_TEMPLATE/feature_request.md`
- `PULL_REQUEST_TEMPLATE.md`

Keeping templates up-to-date ensures new contributors provide actionable detail.
