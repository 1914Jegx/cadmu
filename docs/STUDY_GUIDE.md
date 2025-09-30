# CADMU Study Guide

This study guide explains CADMU from the ground up. It assumes only basic Python
knowledge and walks through the toolkit’s internals using precise terminology and
deliberate pacing.

## 1. Why CADMU Exists

System administrators continuously repeat the same loop: collect data, interpret
it, tidy caches, run updates, schedule maintenance. CADMU codifies that loop into
five verbs—Clean, Audit, Diagnose, Maintain, Update—so you can execute the cycle
consistently.

## 2. Core Building Blocks

### 2.1 `CommandSpec` and `CommandRunner`

`CommandSpec` (in `cadmu.core.runner`) is a dataclass that describes a shell command:

- `command`: the actual argv list or string.
- `sudo`: whether elevation is allowed/required.
- `allow_missing`: whether to skip silently if the binary is absent.
- `env`: environment overrides (used to normalise `$HOME`).
- `optional`: indicates non-critical commands so diagnostics can report them as
  “skipped optional command”.

`CommandRunner.execute` accepts a `CommandSpec`, injects `sudo` when enabled,
invokes `subprocess.run`, and returns a `CommandResult` capturing stdout, stderr,
exit code, and skip metadata.

> **Checkpoint:** understand how `CommandRunner` shields the rest of CADMU from
> `FileNotFoundError` and how it maintains human-readable skip reasons.

### 2.2 `detect_host`

Located in `cadmu.core.system`, this function determines:

- the effective user (e.g. `root` when using `sudo`),
- the owning user (who triggered `sudo`),
- the canonical home directory, and
- distribution metadata parsed from `/etc/os-release`.

These values feed every subcommand to ensure reports land in the correct home
and Arch-only features activate only when appropriate.

### 2.3 Reporting

`cadmu.core.reporting.ReportWriter` writes headers and sections into the report
file while commands stream their output. It prevents interleaving issues and
ensures sections are always separated by consistent markers (`===== section =====`).

### 2.4 Table Rendering

`cadmu.core.table.render_table` converts headers plus rows into a width-aware
ASCII table. It wraps long descriptions while keeping columns aligned—critical
for the Arch pacman report where structured guidance is key.

## 3. Module Walkthroughs

### 3.1 Diagnostics

- `DiagnosticsOptions` toggles optional commands and Arch-specific sections.
- `_baseline_sections` returns a list of `(section, command_specs)` pairs.
- `_run_commands` iterates each command, calls the runner, and writes either the
  output or a skip notice to the report.
- Optional commands are suppressed when the CLI receives `--no-optional`.

### 3.2 Audit

- `_check_storage` inspects filesystem usage using Python’s `shutil.disk_usage`.
- `_check_memory` parses `/proc/meminfo` to detect low `MemAvailable` or high
  swap utilisation.
- `_check_service_failures` calls `systemctl --failed` and reports failing units.
- `_check_arch_packages` and `_check_btrfs_usage` execute only when the host is
  identified as Arch-based.
- Each check returns `AuditFinding` objects. The CLI prints severity-tagged
  bullet points with remediation guidance.

### 3.3 Cleaning

- `planned_actions` returns a list of `CleanupAction` descriptors. Examples:
  `pip cache purge`, `npm cache clean`, `docker system prune`.
- Each action carries a risk level. High-risk actions (like `pacman -Scc`) are
  skipped unless `--allow-high-risk` is provided.

### 3.4 Maintenance

- Exposes `MaintenanceTask` objects (journal vacuum, tmpfiles clean, SMART test,
  Btrfs balance, pacman DB optimise). The CLI prints the recommended frequency
  and optionally executes them.

### 3.5 Updating

- `detect_package_managers` checks for binaries on `$PATH`.
- `build_update_plan` assembles an ordered list of `UpdateStep` objects.
- `execute_update_plan` streams progress and captures status per step.

### 3.6 Arch Pacman Toolkit

- `get_explicit_packages` runs `pacman -Qet` to list explicit packages.
- `collect_explicit_infos` fetches `PackageInfo` objects by chunking `pacman -Qi`
  and `pacman -Si` calls. Each `PackageInfo` stores dependencies, optional deps,
  install date (parsed into UTC), repository, and whether it is foreign (`pacman
  -Qm`).
- `classify_stability` inspects repository lineage (`core`, `extra`, `community`,
  foreign/AUR).
- `classify_difficulty` derives removal difficulty from dependency counts.
- `age_label` bins install age into `New`, `Recent`, `Established`, `Legacy`.
- `build_explicit_package_table` renders a table combining the above signals.
- `top_oldest_packages` exposes the five eldest explicit packages for quick
  remediation targeting.

## 4. CLI Behaviour Deep Dive

`cadmu.cli` wires together argparse subcommands. Each handler:

1. Instantiates a `CommandRunner` (with `sudo` if requested).
2. Collects data via module functions.
3. Prints human-readable output or writes reports.
4. Gracefully handles module-specific exceptions (e.g. `PacmanDataError`).

The new `arch` subcommand requires `--pacman` and currently supports
`--explicit-installed` with optional `--recommendations` and `--limit`.

## 5. Development Workflow

1. Clone the repository and install the development extras:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .[dev]
   ```
2. Run formatting and linting with Ruff:
   ```bash
   ruff check .
   ```
3. Execute tests with coverage:
   ```bash
   pytest
   ```
4. Use the example CLI invocations in `docs/USAGE.md` to validate behaviour.

## 6. Study Recommendations

- Compare `docs/REFERENCE.md` with this guide to map technical terminology to
  conceptual understanding.
- Experiment with the Arch toolkit on a live Arch system to see the recommendation
  heuristics in action.
- Review the tests (under `tests/`) once added to see how modules are mocked and
  verified.

By mastering these modules you can confidently extend CADMU with new platform
integrations or automation routines.
