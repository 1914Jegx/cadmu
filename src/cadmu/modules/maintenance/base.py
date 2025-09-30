from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence

from cadmu.core.runner import CommandRunner, CommandSpec
from cadmu.core.system import is_arch


@dataclass(slots=True)
class MaintenanceTask:
    identifier: str
    description: str
    command: Sequence[str] | str
    frequency: str
    requires_root: bool = False


def recommended_tasks(os_release: dict[str, str] | None = None) -> List[MaintenanceTask]:
    tasks: List[MaintenanceTask] = [
        MaintenanceTask(
            identifier="journal-vacuum",
            description="Vacuum systemd journals to 200M",
            command=["journalctl", "--vacuum-size=200M"],
            frequency="monthly",
            requires_root=True,
        ),
        MaintenanceTask(
            identifier="tmpfiles-clean",
            description="Apply tmpfiles cleanup",
            command=["systemd-tmpfiles", "--clean"],
            frequency="weekly",
            requires_root=True,
        ),
        MaintenanceTask(
            identifier="smart-short",
            description="Run SMART short self-test on /dev/sda",
            command=["smartctl", "-t", "short", "/dev/sda"],
            frequency="monthly",
            requires_root=True,
        ),
    ]
    if os_release and is_arch(os_release):
        tasks.extend(
            [
                MaintenanceTask(
                    identifier="btrfs-balance",
                    description="Btrfs partial balance (-dusage=75 -musage=50)",
                    command=["btrfs", "balance", "start", "-dusage=75", "-musage=50", "/"],
                    frequency="quarterly",
                    requires_root=True,
                ),
                MaintenanceTask(
                    identifier="pacman-db-optimize",
                    description="Optimise pacman database",
                    command=["pacman", "-D", "--asdeps"],
                    frequency="quarterly",
                    requires_root=True,
                ),
            ]
        )
    return tasks


def execute_tasks(runner: CommandRunner, tasks: Iterable[MaintenanceTask]) -> List[tuple[MaintenanceTask, str]]:
    outcomes: List[tuple[MaintenanceTask, str]] = []
    for task in tasks:
        spec = CommandSpec(
            label=task.identifier,
            command=task.command,
            sudo=task.requires_root,
            allow_missing=True,
        )
        try:
            result = runner.execute(spec)
        except FileNotFoundError:
            outcomes.append((task, "skipped (command missing)"))
            continue
        if result.skipped:
            outcomes.append((task, result.reason or "skipped"))
        else:
            outcomes.append((task, "success" if result.exit_code == 0 else f"failed (exit {result.exit_code})"))
    return outcomes
