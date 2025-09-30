from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from cadmu.core.runner import CommandRunner, CommandSpec
from cadmu.core.system import is_arch, supports_systemd


@dataclass(slots=True)
class AuditFinding:
    severity: str
    category: str
    summary: str
    remediation: str | None = None
    detail: str | None = None


@dataclass(slots=True)
class AuditOptions:
    home: Path
    os_release: dict[str, str]


def run_audit(runner: CommandRunner, options: AuditOptions) -> List[AuditFinding]:
    findings: List[AuditFinding] = []
    findings.extend(_check_storage(options))
    findings.extend(_check_memory())
    findings.extend(_check_service_failures(runner))
    if is_arch(options.os_release):
        findings.extend(_check_arch_packages(runner))
        findings.extend(_check_btrfs_usage(runner))
    return findings


def _check_storage(options: AuditOptions) -> Iterable[AuditFinding]:
    issues: List[AuditFinding] = []
    for mountpoint, label, warn, crit in [
        (Path("/"), "root", 0.75, 0.90),
        (Path("/boot"), "boot", 0.70, 0.85),
        (options.home, "home", 0.80, 0.92),
    ]:
        if not mountpoint.exists():
            continue
        usage = shutil.disk_usage(mountpoint)
        percent = usage.used / usage.total if usage.total else 0.0
        if percent >= crit:
            issues.append(
                AuditFinding(
                    severity="critical",
                    category="storage",
                    summary=f"{label} filesystem {percent:.0%} full",
                    remediation=f"Free space on {mountpoint} (remove caches, grow partition, or move data)",
                )
            )
        elif percent >= warn:
            issues.append(
                AuditFinding(
                    severity="warning",
                    category="storage",
                    summary=f"{label} filesystem {percent:.0%} full",
                    remediation=f"Consider cleaning old files on {mountpoint}",
                )
            )
    return issues


def _check_memory() -> Iterable[AuditFinding]:
    meminfo = Path("/proc/meminfo")
    if not meminfo.exists():
        return []
    values: dict[str, int] = {}
    for line in meminfo.read_text().splitlines():
        key, _, rest = line.partition(":")
        rest = rest.strip().split()[0]
        try:
            values[key] = int(rest)
        except ValueError:
            continue
    findings: List[AuditFinding] = []
    mem_total = values.get("MemTotal", 0)
    mem_available = values.get("MemAvailable", 0)
    swap_free = values.get("SwapFree", 0)
    swap_total = values.get("SwapTotal", 0)
    if mem_total and mem_available / mem_total < 0.20:
        findings.append(
            AuditFinding(
                severity="warning",
                category="memory",
                summary="Available RAM below 20%",
                remediation="Close resource-heavy applications or add swap/RAM",
                detail=f"MemAvailable: {mem_available} kB of {mem_total} kB",
            )
        )
    if swap_total and swap_free / swap_total < 0.10:
        findings.append(
            AuditFinding(
                severity="info",
                category="memory",
                summary="Swap usage exceeds 90%",
                remediation="Investigate runaway processes or expand swap",
                detail=f"SwapFree: {swap_free} kB of {swap_total} kB",
            )
        )
    return findings


def _check_service_failures(runner: CommandRunner) -> Iterable[AuditFinding]:
    if not supports_systemd():
        return []
    spec = CommandSpec(label="systemctl failed", command=["systemctl", "--failed"], allow_missing=False)
    try:
        result = runner.execute(spec)
    except FileNotFoundError:
        return []
    if result.skipped or result.exit_code != 0:
        return []
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    problematic = [
        line
        for line in lines
        if line
        and not line.upper().startswith("UNIT ")
        and "loaded units listed" not in line.lower()
    ]
    if problematic:
        return [
            AuditFinding(
                severity="warning",
                category="services",
                summary="One or more systemd units failed",
                remediation="Review `systemctl --failed` and inspect `journalctl -xe` for details",
                detail="\n".join(problematic[:20]),
            )
        ]
    return []


def _check_arch_packages(runner: CommandRunner) -> Iterable[AuditFinding]:
    findings: List[AuditFinding] = []
    for label, command, summary in [
        ("pacman -Qdt", ["pacman", "-Qdt"], "Orphaned packages present"),
        ("pacman -Qu", ["pacman", "-Qu"], "Pending Arch updates"),
    ]:
        spec = CommandSpec(label=label, command=command, allow_missing=True)
        result = runner.execute(spec)
        if result.skipped:
            continue
        if label.endswith("-Qdt") and result.stdout.strip():
            findings.append(
                AuditFinding(
                    severity="info",
                    category="packages",
                    summary=summary,
                    remediation="Consider `sudo pacman -Rns $(pacman -Qdtq)` after reviewing the list",
                    detail=result.stdout,
                )
            )
        if label.endswith("-Qu") and result.stdout.strip():
            count = len(result.stdout.splitlines())
            findings.append(
                AuditFinding(
                    severity="info",
                    category="packages",
                    summary=f"{count} Arch package(s) can be updated",
                    remediation="Run `sudo pacman -Syu` when ready",
                )
            )
    return findings


def _check_btrfs_usage(runner: CommandRunner) -> Iterable[AuditFinding]:
    spec = CommandSpec(label="btrfs usage", command=["btrfs", "filesystem", "usage", "/"], allow_missing=True, sudo=True)
    result = runner.execute(spec)
    if result.skipped or result.exit_code != 0 or not result.stdout:
        return []
    match = re.search(r"Data,single:\s+Size:(?P<size>[\d\.]+)(?P<size_unit>\w+),\s+Used:(?P<used>[\d\.]+)(?P<unit>\w+)\s+\((?P<pct>[\d\.]+)%\)", result.stdout)
    if not match:
        return []
    pct = float(match.group("pct")) / 100.0
    if pct >= 0.90:
        severity = "critical"
    elif pct >= 0.80:
        severity = "warning"
    else:
        return []
    return [
        AuditFinding(
            severity=severity,
            category="storage",
            summary=f"Btrfs data allocation at {pct:.0%}",
            remediation="Run `sudo btrfs balance start -dusage=75 -musage=50 /` to reclaim space",
            detail=result.stdout,
        )
    ]
