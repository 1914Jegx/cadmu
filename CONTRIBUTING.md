# Contributing to CADMU

Thanks for considering a contribution! This project aims to stay predictable and
transparent, so the workflow is intentionally simple.

## Code of Conduct

Please review `CODE_OF_CONDUCT.md` before participating. By contributing you
agree to uphold the standards described there.

## Getting Started

1. Fork and clone the repository.
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. Install CADMU with development dependencies:
   ```bash
   pip install -e .[dev]
   ```
4. Run the default quality gates before making changes:
   ```bash
   ruff check .
   mypy src
   pytest
   ```

## Development Workflow

- Use feature branches with descriptive names (e.g. `feature/arch-packages-ui`).
- Keep commits focused; rebase on `main` before opening a pull request.
- Update or add tests whenever behaviour changes. We expect unit coverage for
  pure Python logic and simple CLI/E2E tests for orchestration glue.
- Refresh documentation when the public interface changes. The `docs/` folder
  contains multiple “levels” of documentation; update at least the relevant
  section(s) and the reference if applicable.
- Run `python -m compileall src` if you add new modules to ensure there are no
  syntax errors.

## Style Guide

- Formatting/linting: `ruff check .`
- Type checking: `mypy src` (strict on new modules is encouraged)
- Line length: 100 characters (enforced by Ruff)
- Prefer dataclasses or TypedDicts for structured data shared across modules.

## Tests

- Unit tests live under `tests/`. Use pytest fixtures for stubbing heavy shell
  interactions (see `tests/test_arch_pacman.py`).
- Mark slow/E2E scenarios with `@pytest.mark.slow` if they need gating.
- Aim for >90% coverage on new modules; the CI workflow reports coverage deltas.

## Pull Requests

Include the following in your PR description:

- Summary of the change
- Testing performed (`pytest`, manual CLI examples)
- Documentation updates (link to docs section or note “not required”)

The CI workflow runs Ruff, mypy, and pytest automatically. Fix all failures
before requesting review.

## Release Planning

For feature releases, update `CHANGELOG.md` with a new entry describing the
change, add an item to `docs/ROADMAP.md` if necessary, and adjust the version in
`pyproject.toml` following semver (major.minor.patch).

Thanks again for contributing!
