# Contributor Onboarding Guide

This guide helps new contributors get productive quickly.

## 1. Local Environment Setup

1. Fork the repository on GitHub and clone your fork.
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   make install  # equivalent to pip install -e .[dev]
   ```
4. (Optional) Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

## 2. Running Quality Gates

Use the provided Makefile targets:

- `make lint` – Ruff static analysis
- `make format` – Ruff formatting
- `make type` – mypy type checks
- `make test` – pytest suite
- `make qa` – all of the above in sequence

CI runs the same commands, so ensure they pass locally before pushing.

## 3. Typical Contribution Flow

1. Create a branch (`git checkout -b feature/<short-description>`).
2. Implement the change, keeping commits focused and well-described.
3. Update or create tests. For shell-heavy modules, stub `CommandRunner`
   (see `tests/test_arch_pacman.py`).
4. Update documentation under `docs/` and the README if behaviour changes.
5. Run `make qa`.
6. Push the branch and open a Pull Request referencing relevant issues.
7. Fill in the PR template, including manual testing notes when applicable.

## 4. Adding Documentation

- Place new guides in `docs/` and cross-link them from `docs/INDEX.md`.
- Keep explanations in three tiers when feasible: quick summary, detailed
  reference, and tutorial-style learning path.

## 5. Writing Issues

Helpful issues include:

- Context/goal
- Proposed approach and acceptance criteria
- References to relevant modules or documentation
- Suggested labels (bug, enhancement, good first issue)

The repository’s `docs/ISSUE_CATALOG.md` lists seeding ideas.

## 6. Release Checklist

When preparing a release:

- Update `CHANGELOG.md`
- Bump `version` in `pyproject.toml`
- Ensure CI is green on the release branch
- Tag the commit (`git tag -a vX.Y.Z -m "Release X.Y.Z"`)
- Push tags and draft release notes on GitHub

Happy hacking!
