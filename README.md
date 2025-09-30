# CADMU

![CADMU logo](docs/assets/cadmu.png)

[![CI](https://github.com/jegx/cadmu/actions/workflows/ci.yml/badge.svg)](https://github.com/jegx/cadmu/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Docs](https://img.shields.io/badge/docs-website-blue.svg)](https://1914jegx.github.io/cadmu/)
[![Discussions](https://img.shields.io/badge/discussions-join-blueviolet.svg)](https://github.com/1914Jegx/cadmu/discussions)
[![Roadmap](https://img.shields.io/badge/roadmap-project%205-brightgreen.svg)](https://github.com/users/1914Jegx/projects/5)

**CADMU** stands for **Clean, Audit, Diagnose, Maintain, Update** – a modular system
health toolkit designed for Linux desktops and servers with first-class Arch Linux
support. CADMU provides a single command line entry point that can:

- Produce comprehensive diagnostic and inventory reports
- Run health and configuration audits with actionable findings
- Recommend and optionally execute maintenance and cleanup routines
- Coordinate safe update workflows across multiple package managers

The project is intentionally modular so you can customise, extend, or disable
features depending on your environment.

## Installation

CADMU works with Python 3.10 or newer. Install from Git directly:

```bash
python -m venv .venv
source .venv/bin/activate
pip install git+https://github.com/jegx/cadmu.git
```

For local development and contributions use editable mode with dev extras:

```bash
pip install -e .[dev]
```

## Documentation

| Guide | Description |
|-------|-------------|
| [Usage](docs/USAGE.md) | Command-by-command examples |
| [Reference](docs/REFERENCE.md) | Deep technical internals |
| [Summary](docs/SUMMARY.md) | Simplified explanations |
| [Study Guide](docs/STUDY_GUIDE.md) | Tutorial-style walk-through |
| [Solutions](docs/SOLUTIONS.md) | Operational playbook |
| [Contributor Guide](docs/CONTRIBUTOR_GUIDE.md) | Onboarding for new contributors |
| [Automation](docs/AUTOMATION.md) | CI/local automation details |
| [Issue Catalog](docs/ISSUE_CATALOG.md) | Backlog seeding ideas |
| [Roadmap](docs/ROADMAP.md) | Upcoming milestones |
| [Docs Site](https://1914jegx.github.io/cadmu/) | Rendered GitHub Pages documentation |

## Branding & Social

- Repository logo: `docs/assets/cadmu.png`
- Social banner (1280×640): `docs/assets/social-banner.png`
- Reminder: upload the banner via **Settings → General → Social preview** (see [#19](https://github.com/1914Jegx/cadmu/issues/19))

## Project Goals

1. **Portable baseline** – Everything should work on any modern Linux (systemd or
   sysvinit) with graceful degradation when tooling is unavailable.
2. **Arch specialisation** – Additional modules unlock when CADMU detects Arch
   derivatives, offering pacman/paru integration and Btrfs-aware maintenance.
3. **Transparency first** – CADMU prefers to *show* planned actions and gather
   consent before making changes. Commands that modify the system are opt-in.
4. **Composable building blocks** – Each subsystem exposes Python APIs so the
   toolkit can be embedded in other workflows or automated pipelines.

## Quick Start

```bash
# Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate

# Install CADMU in editable mode
pip install -e .

# Show available top-level commands
cadmu --help

# Generate a diagnostic report (prints the output path)
cadmu diag --compress

# Run audits without making changes
cadmu audit

# Preview cleanup actions without executing them
cadmu clean --dry-run

# Inspect Arch explicit packages with heuristics
cadmu arch --pacman --explicit-installed --recommendations

# Coordinate updates (auto-detects package manager)
cadmu update --dry-run
```

> **Note**: Some diagnostics require elevated privileges. CADMU never escalates
> automatically; use `sudo cadmu ...` when you want root-only checks.

## Repository Layout

```
src/cadmu/
  cli.py                 # Entry point wiring subcommands
  core/                  # Shared utilities (reporting, command runners, detection)
  modules/
    diagnostics/         # System inventory collectors (generic + Arch)
    audit/               # Health checks producing findings
    maintenance/         # Low-risk maintenance helpers
    cleaning/            # Cache pruning & disk reclamation routines
    updating/            # Package manager orchestration
resources/               # Static templates & shell snippets
```

Each module exports a small API surface that the CLI imports lazily. This makes it
straightforward to extend behaviour by adding new modules or swapping components.

## Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for the
full workflow, coding standards, and testing requirements. The TL;DR:

- `ruff check .`, `mypy src`, and `pytest` must pass.
- Update/extend documentation when changing user-facing behaviour.
- Add unit tests or CLI exercises for new features.

## Roadmap & Planning

- Public backlog board: [CADMU Roadmap](https://github.com/users/1914Jegx/projects/5)
- Seeded issues: see [open issues](https://github.com/1914Jegx/cadmu/issues)
- High-level plan lives in [docs/ROADMAP.md](docs/ROADMAP.md)

## License

MIT License – see `LICENSE` for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release notes and version history.
