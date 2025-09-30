from __future__ import annotations

import getpass
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict


@dataclass(frozen=True)
class HostIdentity:
    effective_user: str
    report_owner: str
    home: Path
    os_release: Dict[str, str]


def _parse_os_release() -> Dict[str, str]:
    data: Dict[str, str] = {}
    path = Path("/etc/os-release")
    if not path.exists():
        return data
    for line in path.read_text().splitlines():
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip('"')
        data[key] = value
    return data


def detect_host(report_owner: str | None = None) -> HostIdentity:
    """Return identity details accounting for sudo usage."""
    effective_user = getpass.getuser()
    owner = report_owner or os.environ.get("SUDO_USER") or effective_user

    home = Path(os.environ.get("HOME", ""))
    if not home or home == Path("/root"):
        try:
            home = Path(Path("~" + owner).expanduser())
        except Exception:  # pragma: no cover - defensive
            home = Path.home()
    os_release = _parse_os_release()
    return HostIdentity(effective_user=effective_user, report_owner=owner, home=home, os_release=os_release)


def is_arch(os_release: Dict[str, str] | None = None) -> bool:
    info = os_release or _parse_os_release()
    distro_id = info.get("ID", "").lower()
    like = info.get("ID_LIKE", "").lower()
    return distro_id == "arch" or "arch" in like


def supports_systemd() -> bool:
    return Path("/run/systemd/system").exists()


def default_report_path(home: Path, prefix: str) -> Path:
    directory = home / "diagnostic_reports"
    directory.mkdir(parents=True, exist_ok=True)
    return directory / prefix
