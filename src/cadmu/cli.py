from __future__ import annotations

import argparse
import os
import tarfile
from datetime import datetime
from pathlib import Path
from typing import Iterable

from cadmu import __version__
from cadmu.core.reporting import report_writer
from cadmu.core.runner import CommandRunner
from cadmu.core.system import default_report_path, detect_host, is_arch
from cadmu.modules.arch import pacman as arch_pacman
from cadmu.modules.audit.base import AuditOptions, run_audit
from cadmu.modules.cleaning.base import CleanupAction, CleanupOptions, execute_actions, planned_actions
from cadmu.modules.diagnostics import arch as arch_diag
from cadmu.modules.diagnostics.base import DiagnosticsOptions, run_diagnostics
from cadmu.modules.maintenance.base import execute_tasks, recommended_tasks
from cadmu.modules.updating.base import build_update_plan, execute_update_plan


def main() -> None:
    parser = argparse.ArgumentParser(prog="cadmu", description="Clean, Audit, Diagnose, Maintain, Update toolkit")
    parser.add_argument("--version", action="version", version=f"cadmu {__version__}")

    subparsers = parser.add_subparsers(dest="command", required=True)

    diag_parser = subparsers.add_parser("diag", help="Generate a diagnostic report")
    diag_parser.add_argument("--output", type=Path, help="Explicit output file path (.txt)")
    diag_parser.add_argument("--compress", action="store_true", help="Additionally create a .tar.gz archive")
    diag_parser.add_argument("--skip-arch", action="store_true", help="Skip Arch-specific diagnostics")
    diag_parser.add_argument("--no-optional", action="store_true", help="Skip optional diagnostics")
    diag_parser.add_argument("--sudo", action="store_true", help="Allow CADMU to use sudo for privileged commands")

    audit_parser = subparsers.add_parser("audit", help="Run health audits and print findings")
    audit_parser.add_argument("--sudo", action="store_true", help="Allow sudo for commands that require it")

    clean_parser = subparsers.add_parser("clean", help="List or execute cleanup routines")
    clean_parser.add_argument("--execute", action="store_true", help="Execute the proposed cleanup actions")
    clean_parser.add_argument("--allow-high-risk", action="store_true", help="Include high-risk cleanup actions")
    clean_parser.add_argument("--sudo", action="store_true", help="Allow sudo for cleanup actions that require it")

    maint_parser = subparsers.add_parser("maintain", help="Run periodic maintenance tasks")
    maint_parser.add_argument("--execute", action="store_true", help="Execute recommended maintenance tasks")
    maint_parser.add_argument("--sudo", action="store_true", help="Allow sudo where required")

    update_parser = subparsers.add_parser("update", help="Coordinate package manager updates")
    update_parser.add_argument("--execute", action="store_true", help="Run update commands instead of printing them")
    update_parser.add_argument("--sudo", action="store_true", help="Allow sudo for update commands")

    arch_parser = subparsers.add_parser("arch", help="Arch Linux focused tooling")
    arch_parser.add_argument("--pacman", action="store_true", help="Enable pacman dataset outputs")
    arch_parser.add_argument("--explicit-installed", action="store_true", help="Summarise explicitly installed packages")
    arch_parser.add_argument("--recommendations", action="store_true", help="Include recommendation columns")
    arch_parser.add_argument("--limit", type=int, default=None, help="Limit number of rows displayed")
    arch_parser.add_argument("--sudo", action="store_true", help="Allow sudo for privileged arch commands")

    args = parser.parse_args()

    identity = detect_host()
    runner = CommandRunner(use_sudo=args.sudo or os.geteuid() == 0)

    if args.command == "diag":
        handle_diag(args, identity, runner)
    elif args.command == "audit":
        handle_audit(args, identity, runner)
    elif args.command == "clean":
        handle_clean(args, identity, runner)
    elif args.command == "maintain":
        handle_maintain(args, identity, runner)
    elif args.command == "update":
        handle_update(args, identity, runner)
    elif args.command == "arch":
        arch_runner = CommandRunner(use_sudo=args.sudo or os.geteuid() == 0)
        handle_arch(args, identity, arch_runner)


def handle_diag(args: argparse.Namespace, identity, runner: CommandRunner) -> None:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    filename = args.output or default_report_path(identity.home, f"cadmu-diagnostic-{timestamp}.txt")
    filename.parent.mkdir(parents=True, exist_ok=True)

    include_arch = not args.skip_arch and is_arch(identity.os_release)
    options = DiagnosticsOptions(home=identity.home, include_optional=not args.no_optional, include_arch=include_arch)

    arch_sections = arch_diag.arch_sections(options) if include_arch else None

    with report_writer(filename, host=os.uname().nodename, effective_user=identity.effective_user, owner=identity.report_owner) as writer:
        run_diagnostics(writer, runner, options, arch_sections=arch_sections)

    archive_path: Path | None = None
    if args.compress:
        archive_path = filename.with_suffix(".tar.gz")
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(filename, arcname=filename.name)

    print(f"Diagnostic report written to {filename}")
    if archive_path:
        print(f"Compressed archive created at {archive_path}")


def handle_audit(args: argparse.Namespace, identity, runner: CommandRunner) -> None:
    findings = run_audit(runner, AuditOptions(home=identity.home, os_release=identity.os_release))
    if not findings:
        print("No audit findings detected. System looks healthy!")
        return
    for finding in findings:
        header = f"[{finding.severity.upper()}] {finding.category}: {finding.summary}"
        print(header)
        if finding.detail:
            print(f"  details: {finding.detail}")
        if finding.remediation:
            print(f"  fix: {finding.remediation}")
        print()


def handle_clean(args: argparse.Namespace, identity, runner: CommandRunner) -> None:
    options = CleanupOptions(include_high_risk=args.allow_high_risk, os_release=identity.os_release)
    actions = planned_actions(options)
    if not args.execute:
        _print_cleanup_plan(actions)
        print("\nUse --execute to run the low-risk actions automatically.")
        return
    results = execute_actions(runner, actions, include_high_risk=args.allow_high_risk)
    for action, status in results:
        print(f"{action.identifier}: {status}")


def _print_cleanup_plan(actions: Iterable[CleanupAction]) -> None:
    print("Cleanup plan:")
    for action in actions:
        cmd = action.command if isinstance(action.command, str) else " ".join(action.command)
        risk = action.risk
        notes = f" ({action.notes})" if action.notes else ""
        prefix = "*" if risk == "low" else "-"
        print(f" {prefix} [{risk}] {action.description}: {cmd}{notes}")


def handle_maintain(args: argparse.Namespace, identity, runner: CommandRunner) -> None:
    tasks = recommended_tasks(identity.os_release)
    if not args.execute:
        print("Recommended maintenance tasks:")
        for task in tasks:
            cmd = task.command if isinstance(task.command, str) else " ".join(task.command)
            print(f" - ({task.frequency}) {task.description}: {cmd}")
        print("\nUse --execute to run the available tasks now.")
        return
    outcomes = execute_tasks(runner, tasks)
    for task, status in outcomes:
        print(f"{task.identifier}: {status}")


def handle_update(args: argparse.Namespace, identity, runner: CommandRunner) -> None:
    plan = build_update_plan(identity.os_release)
    if not plan:
        print("No supported package managers detected.")
        return
    if not args.execute:
        print("Planned update steps:")
        for step in plan:
            cmd = step.command if isinstance(step.command, str) else " ".join(step.command)
            print(f" - {step.description}: {cmd}")
        print("\nUse --execute to run the update steps in order.")
        return
    results = execute_update_plan(runner, plan)
    for step, status in results:
        cmd = step.command if isinstance(step.command, str) else " ".join(step.command)
        print(f"{step.description}: {status} ({cmd})")


def handle_arch(args: argparse.Namespace, identity, runner: CommandRunner) -> None:
    if not args.pacman:
        print("No data source selected. Use --pacman to query pacman insights.")
        return

    if not args.explicit_installed:
        print("Currently only --explicit-installed is supported. Use --explicit-installed to list packages.")
        return

    try:
        infos = arch_pacman.collect_explicit_infos(runner)
    except arch_pacman.PacmanDataError as exc:  # type: ignore[attr-defined]
        print(f"Failed to query pacman data: {exc}")
        return

    table = arch_pacman.build_explicit_package_table(
        runner,
        include_recommendations=args.recommendations,
        limit=args.limit,
        infos=infos,
    )
    print(table)

    oldest = arch_pacman.top_oldest_packages(infos)
    if oldest:
        print("\nOldest explicit installs:")
        for info in oldest:
            age = arch_pacman.age_label(info)
            stability = arch_pacman.classify_stability(info)
            print(f" - {info.name} ({info.version}) • {age} • {stability}")


if __name__ == "__main__":  # pragma: no cover
    main()
