# Operational Solutions with CADMU

This document synthesises recommended actions derived from CADMU’s capabilities.
Use it as a playbook when responding to real-world maintenance scenarios.

## 1. Routine Upgrade Cadence

1. `cadmu diag --no-optional` – baseline state without long-running queries.
2. `cadmu audit` – review highlighted risks (disk, memory, services).
3. `cadmu arch --pacman --explicit-installed --recommendations --limit 50` –
   identify legacy or unstable packages before updating.
4. `cadmu clean` – free cache space pre-upgrade; follow with
   `cadmu clean --execute --allow-high-risk` if additional space is required.
5. `cadmu update --execute --sudo` – perform synchronised package updates.
6. `cadmu maintain --execute --sudo` – run journald vacuum, tmpfiles cleanup,
   and SMART quick tests to confirm system health post-upgrade.

## 2. Disk Pressure Response

- Diagnose breadth: `cadmu diag --skip-arch --compress` and review the report.
- Trim caches safely: `cadmu clean --execute`.
- If still constrained, escalate: `cadmu clean --execute --allow-high-risk` to
  purge pacman sync caches, followed by a targeted review of explicit packages
  via `cadmu arch ... --recommendations` to decommission redundant software.

## 3. Service Resilience

- Use `cadmu audit --sudo` to surface failing units.
- For each failing unit, consult the diagnostic report’s journal sections.
- Consider adding `systemctl status <unit>` to the diagnostics module if you
  routinely investigate the same services.

## 4. Pacman Hygiene (Arch)

| Objective | CADMU Command | Outcome |
|-----------|---------------|---------|
| Inventory explicit packages | `cadmu arch --pacman --explicit-installed` | List with versions/descriptions |
| Prioritise remediation | `cadmu arch ... --recommendations` | Adds stability, difficulty, age heuristics |
| Spot long-lived packages | Review “Oldest explicit installs” footer | Targets technical debt |
| Validate foreign/AUR packages | Check stability column for “AUR/External” | Focus on verifying upstream health |

Recommendations or heuristics are intentionally conservative: `Tier-0` packages
map to the base system and should rarely be removed, while `AUR/External`
entries deserve regular validation.

## 5. Continuous Compliance

Integrate CADMU into automation pipelines:

- Run `cadmu diag` nightly with `--compress` and archive the report artefacts.
- Trigger `cadmu audit` after system changes to catch regressions early.
- Schedule `cadmu maintain --execute` weekly under a privileged service account.
- Use outputs from `cadmu arch` to populate CMDB entries about package provenance
  and age for compliance documentation.

## 6. Extensibility Checklist

When extending CADMU for new platforms or routines:

1. Model shell interactions as `CommandSpec` instances.
2. Provide preview and execution modes; respect `allow_missing=True` for optional
   tooling.
3. Capture remediation guidance in the audit layer so operators know what to do.
4. Document the new behaviour in both the technical reference and the simplified
   guides to keep knowledge consistent.

These practices maintain CADMU’s balance between transparency, safety, and
actionability.
