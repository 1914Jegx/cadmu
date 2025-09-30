from __future__ import annotations

from typing import Iterable, List

from cadmu.core.runner import CommandSpec
from cadmu.modules.diagnostics.base import _cmd, _home_env, DiagnosticsOptions


def arch_sections(options: DiagnosticsOptions) -> List[tuple[str, Iterable[CommandSpec]]]:
    env_home = _home_env(options.home)
    return [
        (
            "Arch Package Management",
            [
                _cmd("pacman -Q", ["pacman", "-Q"], sudo=False),
                _cmd("pacman -Qu", ["pacman", "-Qu"], sudo=False, allow_missing=True),
                _cmd("pacman -Qdt", ["pacman", "-Qdt"], sudo=False, allow_missing=True),
                _cmd("paru -Qtdq", ["paru", "-Qtdq"], sudo=False, allow_missing=True),
                _cmd("paru -Qu", ["paru", "-Qu"], sudo=False, allow_missing=True),
                _cmd("paccache", ["paccache", "--dryrun"], sudo=False, allow_missing=True),
            ],
        ),
        (
            "Arch Btrfs Insights",
            [
                _cmd("btrfs usage /", ["btrfs", "filesystem", "usage", "/"], sudo=True, allow_missing=True),
                _cmd("btrfs df /", ["btrfs", "filesystem", "df", "/"], sudo=True, allow_missing=True),
            ],
        ),
        (
            "Arch Recent Changes",
            [
                _cmd("pacman log", ["tail", "-n", "200", "/var/log/pacman.log"], sudo=True, allow_missing=True),
                _cmd("mkinitcpio presets", ["bash", "-lc", "ls /etc/mkinitcpio.d 2>/dev/null"], sudo=False, allow_missing=True),
            ],
        ),
        (
            "Per-user Caches",
            [
                _cmd("paru cache", ["bash", "-lc", "du -sh $HOME/.cache/paru 2>/dev/null"], env=env_home, allow_missing=True),
                _cmd("pip cache", ["pip", "cache", "info"], allow_missing=True),
                _cmd("npm cache", ["npm", "cache", "verify"], allow_missing=True),
                _cmd("docker system df", ["docker", "system", "df"], allow_missing=True),
                _cmd("docker ps", ["docker", "ps", "-a"], allow_missing=True),
            ],
        ),
    ]
