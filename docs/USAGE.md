# CADMU Usage Guide

CADMU exposes a single CLI entry point with sub-commands that map to each part of
the Clean–Audit–Diagnose–Maintain–Update workflow. All commands support
`--help` for inline documentation.

```text
usage: cadmu [-h] [--version] {diag,audit,clean,maintain,update} ...
```

## Diagnostics (`cadmu diag`)

Produce a timestamped system report. By default CADMU writes to
`~/diagnostic_reports/cadmu-diagnostic-<timestamp>.txt`.

Options of note:

- `--compress` – also produce a `.tar.gz` containing the report.
- `--skip-arch` – disable Arch-specific collectors when running on derivatives.
- `--no-optional` – skip expensive/non-essential commands (logs, package listings).
- `--sudo` – allow CADMU to prefix privileged commands with `sudo`.

```bash
cadmu diag --compress --sudo
```

## Auditing (`cadmu audit`)

Runs quick heuristics for disk pressure, memory constraints, systemd failures,
and (on Arch) pending updates/orphaned packages. Output is printed to stdout. Use
`--sudo` to let the audit inspect service failures.

```bash
cadmu audit --sudo
```

## Cleaning (`cadmu clean`)

Shows cache and artifact pruning actions with risk classifications. Without
flags it prints a plan; use `--execute` to run low-risk commands automatically
and `--allow-high-risk` to include destructive steps such as `pacman -Scc`.

```bash
cadmu clean           # preview
cadmu clean --execute # run low/medium risk actions
```

## Maintenance (`cadmu maintain`)

Lists periodic chores (journal vacuuming, SMART tests, Btrfs balances on Arch).
Use `--execute` alongside `--sudo` to run them immediately.

```bash
cadmu maintain --execute --sudo
```

## Updates (`cadmu update`)

Detects installed package managers (pacman, apt, dnf, zypper, etc.) and prints
an ordered update plan. Run with `--execute` to perform the updates using the
current session’s privileges.

```bash
cadmu update          # preview
cadmu update --execute --sudo
```

## Arch Toolkit (`cadmu arch`)

Activates Arch-specific tooling. Currently the pacman data source is supported
with explicit package analysis and heuristic recommendations.

```bash
# Summarise explicit packages with stability/difficulty/age insights
cadmu arch --pacman --explicit-installed --recommendations --limit 40

# Quick inventory without heuristics
cadmu arch --pacman --explicit-installed --limit 20
```

Columns returned when `--recommendations` is present:

| Column | Meaning |
|--------|---------|
| General | High-level recommendation derived from repository provenance |
| Difficulty | Ease of removing/replacing the package based on dependency fan-out |
| Stability | Repository tier or “AUR/External” classification |
| Age | Relative install age bucket (new, recent, established, legacy) |

## Tips

- CADMU never assumes privilege escalation. When you expect commands to require
  root access, wrap the invocation with `sudo` or pass `--sudo`.
- Reports are plain text. Use the `docs/templates` directory (coming soon) to
  customise section ordering or command sets.
- Extend CADMU by creating new modules under `src/cadmu/modules/` and wiring
  them from `cli.py`.
