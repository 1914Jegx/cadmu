from __future__ import annotations

import shutil
from dataclasses import dataclass
from typing import Iterable, List, Sequence

from cadmu.core.runner import CommandRunner, CommandSpec
from cadmu.core.system import is_arch


@dataclass(slots=True)
class CleanupAction:
    identifier: str
    description: str
    command: Sequence[str] | str
    requires_root: bool = False
    risk: str = "low"  # low, medium, high
    notes: str | None = None


@dataclass(slots=True)
class CleanupOptions:
    include_high_risk: bool = False
    os_release: dict[str, str] | None = None


def planned_actions(options: CleanupOptions) -> List[CleanupAction]:
    actions: List[CleanupAction] = [
        CleanupAction(
            identifier="pip-cache",
            description="Purge pip cache",
            command=["pip", "cache", "purge"],
            notes="Re-downloads wheels on next install",
        ),
        CleanupAction(
            identifier="npm-cache",
            description="Clean npm cache",
            command=["npm", "cache", "clean", "--force"],
            notes="npm recreates the cache automatically",
        ),
        CleanupAction(
            identifier="pnpm-store",
            description="Prune pnpm global store",
            command=["pnpm", "store", "prune"],
        ),
        CleanupAction(
            identifier="pipx",
            description="Prune pipx shared libraries",
            command=["pipx", "reinstall-all"],
            risk="medium",
            notes="Rebuilds pipx-managed apps; may take time",
        ),
        CleanupAction(
            identifier="docker-prune",
            description="Prune unused Docker data",
            command=["docker", "system", "prune", "-f"],
            risk="medium",
            notes="Removes dangling images/containers; add --volumes for deeper cleanup",
        ),
    ]

    if options.os_release and is_arch(options.os_release):
        actions.extend(
            [
                CleanupAction(
                    identifier="pacman-cache",
                    description="Drop unused pacman packages",
                    command=["paccache", "-ruk2"],
                    requires_root=True,
                    risk="low",
                ),
                CleanupAction(
                    identifier="pacman-sync",
                    description="Purge pacman sync cache",
                    command=["pacman", "-Scc"],
                    requires_root=True,
                    risk="high",
                    notes="Deletes ALL cached packages – rerun downloads if downgrading",
                ),
                CleanupAction(
                    identifier="paru-cache",
                    description="Clear paru build cache",
                    command=["paru", "-Scc"],
                    risk="medium",
                ),
            ]
        )
    return actions


def execute_actions(runner: CommandRunner, actions: Iterable[CleanupAction], *, include_high_risk: bool = False) -> List[tuple[CleanupAction, str]]:
    results: List[tuple[CleanupAction, str]] = []
    for action in actions:
        if action.risk == "high" and not include_high_risk:
            results.append((action, "skipped (high risk not enabled)"))
            continue
        command = action.command
        spec = CommandSpec(
            label=action.identifier,
            command=command,
            sudo=action.requires_root,
            allow_missing=True,
            shell=isinstance(command, str),
        )
        if isinstance(command, Sequence) and shutil.which(command[0]) is None:
            results.append((action, "skipped (command missing)"))
            continue
        result = runner.execute(spec)
        if result.skipped:
            summary = result.reason or "skipped"
        else:
            summary = "success" if result.exit_code == 0 else f"failed (exit {result.exit_code})"
        results.append((action, summary))
    return results
