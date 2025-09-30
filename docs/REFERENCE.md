# CADMU Technical Reference

This document captures the implementation details of CADMU (Clean, Audit, Diagnose,
Maintain, Update). It is intended for maintainers who require a precise and
technical understanding of the codebase.

## Architectural Overview

CADMU is a modular Python package built around a small core that handles
identity detection, command execution, structured reporting, and table
rendering. Feature modules compose these primitives to implement higher-level
operations.

```
cadmu/
├── cli.py                 # Argparse router and orchestration
├── core/
│   ├── system.py          # Host detection, Arch detection, report paths
│   ├── runner.py          # CommandSpec abstraction + sudo-aware execution
│   └── table.py           # ASCII table rendering with wrapping
└── modules/
    ├── diagnostics/       # Inventory gathering (generic + Arch overlays)
    ├── audit/             # Heuristic health findings
    ├── cleaning/          # Cache and artefact pruning plans
    ├── maintenance/       # Periodic tasks (journald vacuum, SMART, Btrfs)
    ├── updating/          # Package manager coordination
    └── arch/              # Arch-specific insights (pacman intelligence)
```

The CLI instantiates a `CommandRunner` per invocation. Subcommands request
module functions that receive the runner and structured options. The runner
wraps `subprocess.run`, injects `sudo` automatically when permitted, and returns
`CommandResult` objects preserving stdout, stderr, exit codes, and skip reasons.

## Core Components

### `CommandRunner`

- Accepts `CommandSpec` objects describing the command, whether `sudo` is
  required, whether missing binaries should be tolerated, optional environment
  overrides, timeouts, and optionality status.
- Inserts `sudo` when `use_sudo=True` and gracefully skips execution when
  `sudo` is not allowed or the binary is absent (e.g. optional diagnostics).
- Normalises outputs (`stdout`/`stderr`) and exposes a convenience
  `format_command` helper for human-readable logging.

### `system.detect_host`

- Collapses the effective user and the report owner (handling `sudo` cases).
- Resolves the canonical home directory with fallbacks for `/root` contexts.
- Parses `/etc/os-release` to determine distribution lineage; used by modules
  to activate Arch-only logic.

### `reporting.ReportWriter`

- Serialises structured metadata to disk while streaming command outputs.
- Provides section/subsection helpers to keep reports visually consistent.

### `table.render_table`

- Implements width-aware ASCII tables with configurable column wrapping. Used
  by the Arch pacman command to provide rich tabular output without external
  dependencies.

## Module Highlights

### Diagnostics (`modules/diagnostics`)

- `DiagnosticsOptions` toggles optional vs. Arch sections.
- Command lists are declared as data (`CommandSpec`) making it trivial to audit
  or extend the executed commands.
- Optional commands respect the `--no-optional` CLI switch and record the skip
  in the generated report.

### Audit (`modules/audit`)

- Supplies `AuditFinding` tuples (severity, category, summary, remediation,
  details) allowing the CLI to render actionable results.
- Checks cover storage threshold monitoring, low memory availability, swap
  saturation, systemd unit failures, pending Arch updates, and Btrfs chunk
  utilisation.

### Cleaning (`modules/cleaning`)

- Produces risk-annotated `CleanupAction` items. Execution honours
  `--allow-high-risk` and gracefully skips missing utilities.

### Maintenance (`modules/maintenance`)

- Expresses tasks (journal vacuum, tmpfiles cleanup, SMART, Btrfs balance,
  pacman DB optimisation) with frequency metadata to support scheduling.

### Updating (`modules/updating`)

- Detects installed package managers (`pacman`, `paru`, `apt`, `dnf`,
  `zypper`, `emerge`, `xbps-install`) and synthesises an ordered update plan.

### Arch Tooling (`modules/arch/pacman.py`)

- Provides high-fidelity pacman insights. Key functions:
  - `get_explicit_packages`: retrieves explicitly installed packages.
  - `collect_explicit_infos`: builds `PackageInfo` objects with dependencies,
    install dates, repository origin, and a foreign/AUR flag.
  - `build_explicit_package_table`: renders a rich table with general and
    difficulty-aware recommendations, stability classification, and age
    labelling.
  - `top_oldest_packages`: highlights the longest-installed explicit packages
    to prioritise technical debt reviews.
- Recommendation heuristics blend repository provenance, dependency fan-out,
  and install age to provide actionable triage guidance.

## CLI Surface

| Command | Purpose | Notable Flags |
|---------|---------|---------------|
| `cadmu diag` | Generate diagnostic reports | `--compress`, `--no-optional`, `--skip-arch`, `--sudo` |
| `cadmu audit` | Run health checks | `--sudo` |
| `cadmu clean` | Preview or execute cleanups | `--execute`, `--allow-high-risk`, `--sudo` |
| `cadmu maintain` | Run maintenance tasks | `--execute`, `--sudo` |
| `cadmu update` | Coordinate updates | `--execute`, `--sudo` |
| `cadmu arch` | Arch toolkit | `--pacman`, `--explicit-installed`, `--recommendations`, `--limit`, `--sudo` |

All subcommands default to preview/read-only behaviour unless explicitly asked
to execute potentially destructive actions.

## Error Handling Strategy

- Optional commands are annotated in `CommandSpec.optional=True` so diagnostics
  record that they were intentionally skipped.
- `PacmanDataError` conveys detailed pacman lookup issues and is caught by the
  CLI to present actionable feedback.
- The `CommandRunner` encapsulates `FileNotFoundError` for missing binaries and
  returns `skipped=True` to the caller when `allow_missing=True`.

## Extensibility

- Add new diagnostics by appending `CommandSpec` entries; they automatically
  flow through the reporting system.
- Introduce new Arch tools by extending `cadmu.modules.arch` and registering
  options in `cli.py`.
- Table rendering is reusable for other modules requiring textual reporting.

## Development Tooling

- `pyproject.toml` defines a `dev` extra with `pytest`, `pytest-cov`,
  `coverage`, `ruff`, and `mypy` for linting and testing.
- Coverage configuration is set to branch mode with missing line reporting.
- Ruff enforces a 100-character line limit targeting Python 3.10.

Refer to `docs/STUDY_GUIDE.md` and `docs/SUMMARY.md` for progressively simpler
explanations of the same internals.
