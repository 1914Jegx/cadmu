from __future__ import annotations

import shutil
from dataclasses import dataclass
from typing import Iterable, List


@dataclass(frozen=True)
class Dependency:
    command: str
    package: str
    optional: bool = False
    notes: str | None = None


GENERAL_DEPENDENCIES: List[Dependency] = [
    Dependency("uname", "coreutils"),
    Dependency("lsblk", "util-linux"),
    Dependency("lsusb", "usbutils", optional=True),
    Dependency("lspci", "pciutils", optional=True),
    Dependency("lscpu", "util-linux", optional=True),
    Dependency("sensors", "lm_sensors", optional=True),
    Dependency("loginctl", "systemd", optional=True),
    Dependency("timedatectl", "systemd", optional=True),
    Dependency("journalctl", "systemd", optional=True),
    Dependency("ip", "iproute2"),
    Dependency("ss", "iproute2", optional=True),
    Dependency("nmcli", "networkmanager", optional=True),
    Dependency("docker", "docker", optional=True),
    Dependency("podman", "podman", optional=True),
    Dependency("python", "python", optional=True),
]

ARCH_DEPENDENCIES: List[Dependency] = [
    Dependency("pacman", "pacman"),
    Dependency("paru", "paru", optional=True, notes="Install from AUR"),
    Dependency("btrfs", "btrfs-progs", optional=True),
    Dependency("lsb_release", "lsb-release", optional=True),
    Dependency("paccache", "pacman-contrib", optional=True),
]


def summarise(dependencies: Iterable[Dependency]) -> str:
    lines = []
    for dep in dependencies:
        available = shutil.which(dep.command) is not None
        status = "FOUND" if available else "MISSING"
        detail = f"[{status}] {dep.command} (package: {dep.package})"
        if dep.optional:
            detail += " [optional]"
        if dep.notes:
            detail += f" – {dep.notes}"
        lines.append(detail)
    return "\n".join(lines)
