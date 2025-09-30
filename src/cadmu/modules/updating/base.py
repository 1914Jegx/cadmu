from __future__ import annotations

import shutil
from dataclasses import dataclass
from typing import Iterable, List, Sequence

from cadmu.core.runner import CommandRunner, CommandSpec
from cadmu.core.system import is_arch


@dataclass(slots=True)
class UpdateStep:
    description: str
    command: Sequence[str] | str
    requires_root: bool = True


def detect_package_managers() -> List[str]:
    candidates = [
        "pacman",
        "paru",
        "apt",
        "dnf",
        "zypper",
        "emerge",
        "xbps-install",
    ]
    return [name for name in candidates if shutil.which(name)]


def build_update_plan(os_release: dict[str, str] | None = None) -> List[UpdateStep]:
    pm = detect_package_managers()
    steps: List[UpdateStep] = []
    if "pacman" in pm:
        steps.append(UpdateStep("Synchronise Arch repositories", ["pacman", "-Sy"], True))
        steps.append(UpdateStep("Apply Arch updates", ["pacman", "-Su"], True))
    if "paru" in pm:
        steps.append(UpdateStep("Update AUR packages via paru", ["paru", "-Syu"], True))
    if "apt" in pm:
        steps.append(UpdateStep("Debian/Ubuntu package list refresh", ["apt", "update"], True))
        steps.append(UpdateStep("Debian/Ubuntu upgrade", ["apt", "full-upgrade"], True))
    if "dnf" in pm:
        steps.append(UpdateStep("Fedora dnf upgrade", ["dnf", "upgrade", "-y"], True))
    if "zypper" in pm:
        steps.append(UpdateStep("openSUSE refresh", ["zypper", "ref"], True))
        steps.append(UpdateStep("openSUSE update", ["zypper", "dup"], True))
    if "emerge" in pm:
        steps.append(UpdateStep("Gentoo world update", ["emerge", "--sync"]))
        steps.append(UpdateStep("Gentoo upgrade", ["emerge", "--ask", "--update", "--deep", "--newuse", "@world"], True))
    if "xbps-install" in pm:
        steps.append(UpdateStep("Void Linux update", ["xbps-install", "-Su"], True))

    if os_release and is_arch(os_release) and all(step.command[0] != "btrfs" for step in steps):
        steps.append(UpdateStep("Refresh Arch mirrors (reflector)", ["reflector", "--latest", "20", "--save", "/etc/pacman.d/mirrorlist"], True))
    return steps


def execute_update_plan(runner: CommandRunner, steps: Iterable[UpdateStep]) -> List[tuple[UpdateStep, str]]:
    results: List[tuple[UpdateStep, str]] = []
    for step in steps:
        spec = CommandSpec(
            label=step.description,
            command=step.command,
            sudo=step.requires_root,
            allow_missing=True,
        )
        result = runner.execute(spec)
        if result.skipped:
            summary = result.reason or "skipped"
        else:
            summary = "success" if result.exit_code == 0 else f"failed (exit {result.exit_code})"
        results.append((step, summary))
    return results
