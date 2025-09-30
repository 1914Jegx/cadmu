from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

import pytest

from cadmu.core.runner import CommandResult, CommandSpec
from cadmu.core.system import HostIdentity
from cadmu.modules.arch.pacman import PackageInfo
from cadmu.modules.audit.base import AuditFinding
from cadmu.modules.cleaning.base import CleanupAction
from cadmu.modules.maintenance.base import MaintenanceTask
from cadmu.modules.updating.base import UpdateStep


class RecordingRunner:
    """Collects command specs for assertions without touching the real system."""

    def __init__(self, use_sudo: bool = False) -> None:
        self.use_sudo = use_sudo
        self.executed: list[CommandSpec] = []

    def execute(self, spec: CommandSpec) -> CommandResult:
        self.executed.append(spec)
        if isinstance(spec.command, str):
            command_text = spec.command
        else:
            command_text = " ".join(spec.command)
        label = spec.label or command_text
        return CommandResult(spec=spec, stdout=f"{label} ok", stderr="", exit_code=0)


@pytest.fixture(name="root_enabled")
def fixture_root_enabled() -> bool:
    return os.geteuid() == 0


def test_cli_end_to_end_workflow(monkeypatch: pytest.MonkeyPatch, tmp_path, capsys, root_enabled: bool) -> None:
    from cadmu import cli

    runner_instances: list[RecordingRunner] = []

    def runner_factory(use_sudo: bool = False) -> RecordingRunner:
        runner = RecordingRunner(use_sudo=use_sudo)
        runner_instances.append(runner)
        return runner

    monkeypatch.setattr(cli, "CommandRunner", runner_factory)

    identity = HostIdentity(
        effective_user="tester",
        report_owner="tester",
        home=tmp_path,
        os_release={"ID": "arch"},
    )
    monkeypatch.setattr(cli, "detect_host", lambda: identity)

    diag_context: dict[str, object] = {}

    def fake_run_diagnostics(writer, runner, options, arch_sections=None):
        diag_context["include_optional"] = options.include_optional
        diag_context["include_arch"] = options.include_arch
        diag_context["arch_sections"] = list(arch_sections or [])
        writer.section("Synthetic diagnostics")
        writer.note("Diagnostics executed")

    monkeypatch.setattr(cli, "run_diagnostics", fake_run_diagnostics)
    monkeypatch.setattr(
        cli.arch_diag,
        "arch_sections",
        lambda options: [
            ("Arch Section", [CommandSpec(label="arch-check", command=["echo", "arch"], allow_missing=False)])
        ],
    )

    audit_findings = [
        AuditFinding(
            severity="warning",
            category="storage",
            summary="Root nearly full",
            remediation="Free space",
            detail="root at 92% usage",
        )
    ]
    monkeypatch.setattr(cli, "run_audit", lambda runner, options: audit_findings)

    def fake_planned_actions(options):
        return [
            CleanupAction(
                identifier="pip-cache",
                description="Clear pip cache",
                command=["pip", "cache", "purge"],
                risk="low",
            ),
            CleanupAction(
                identifier="pacman-cache",
                description="Drop pacman cache",
                command=["paccache", "-ruk2"],
                requires_root=True,
                risk="high",
                notes="Removes archived packages",
            ),
        ]

    monkeypatch.setattr(cli, "planned_actions", fake_planned_actions)

    def fake_execute_actions(runner, actions, include_high_risk):
        statuses = []
        for action in actions:
            if action.risk == "high" and not include_high_risk:
                statuses.append((action, "skipped (high risk not enabled)"))
            else:
                suffix = " with sudo" if action.requires_root and runner.use_sudo else ""
                statuses.append((action, f"executed{suffix}"))
        return statuses

    monkeypatch.setattr(cli, "execute_actions", fake_execute_actions)

    def fake_recommended_tasks(os_release):
        return [
            MaintenanceTask(
                identifier="journal",
                description="Vacuum journal",
                command=["journalctl", "--vacuum-size=200M"],
                frequency="monthly",
                requires_root=True,
            ),
            MaintenanceTask(
                identifier="pip-cache-info",
                description="Review pip cache metadata",
                command=["pip", "cache", "info"],
                frequency="weekly",
            ),
        ]

    monkeypatch.setattr(cli, "recommended_tasks", fake_recommended_tasks)

    def fake_execute_tasks(runner, tasks):
        outcomes = []
        for task in tasks:
            suffix = " (sudo)" if task.requires_root and runner.use_sudo else ""
            outcomes.append((task, f"success{suffix}"))
        return outcomes

    monkeypatch.setattr(cli, "execute_tasks", fake_execute_tasks)

    def fake_build_update_plan(os_release):
        return [
            UpdateStep(description="Refresh repositories", command=["pacman", "-Sy"], requires_root=True),
            UpdateStep(description="Upgrade packages", command=["pacman", "-Su"], requires_root=True),
        ]

    monkeypatch.setattr(cli, "build_update_plan", fake_build_update_plan)
    monkeypatch.setattr(
        cli,
        "execute_update_plan",
        lambda runner, steps: [
            (step, "success with sudo" if runner.use_sudo else "success") for step in steps
        ],
    )

    pkg = PackageInfo(
        name="python",
        version="3.13.0",
        description="Python language",
        install_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
        depends=["expat", "gdbm"],
        optional_deps=["sqlite"],
        repo="extra",
        is_foreign=False,
    )
    monkeypatch.setattr(cli.arch_pacman, "collect_explicit_infos", lambda runner: [pkg])
    monkeypatch.setattr(
        cli.arch_pacman,
        "build_explicit_package_table",
        lambda runner, include_recommendations, limit, infos: "PACKAGE TABLE\npython",
    )
    monkeypatch.setattr(cli.arch_pacman, "top_oldest_packages", lambda infos, limit=5: infos[:limit])
    monkeypatch.setattr(cli.arch_pacman, "age_label", lambda info: "450 days old")
    monkeypatch.setattr(cli.arch_pacman, "classify_stability", lambda info: "Tier-1 (Extra)")

    def invoke(argv: list[str]) -> str:
        monkeypatch.setattr(sys, "argv", argv)
        cli.main()
        return capsys.readouterr().out

    diag_path = tmp_path / "diag.txt"
    diag_output = invoke(["cadmu", "diag", "--output", str(diag_path), "--compress"])
    assert diag_path.exists()
    assert diag_path.with_suffix(".tar.gz").exists()
    assert "Diagnostic report written to" in diag_output
    assert "Compressed archive created at" in diag_output
    assert diag_context["include_optional"] is True
    assert diag_context["include_arch"] is True
    assert diag_context["arch_sections"]
    assert runner_instances[-1].use_sudo is root_enabled

    audit_output = invoke(["cadmu", "audit", "--sudo"])
    assert "[WARNING] storage: Root nearly full" in audit_output
    assert "details: root at 92% usage" in audit_output
    assert runner_instances[-1].use_sudo is True

    clean_plan_output = invoke(["cadmu", "clean"])
    assert "Cleanup plan" in clean_plan_output
    assert "Clear pip cache" in clean_plan_output
    assert "Drop pacman cache" in clean_plan_output
    assert "Use --execute to run the low-risk actions automatically." in clean_plan_output
    assert runner_instances[-1].use_sudo is root_enabled

    clean_exec_output = invoke(["cadmu", "clean", "--execute", "--allow-high-risk", "--sudo"])
    assert "pip-cache: executed" in clean_exec_output
    assert "pacman-cache: executed with sudo" in clean_exec_output
    assert runner_instances[-1].use_sudo is True

    maintain_plan_output = invoke(["cadmu", "maintain"])
    assert "Recommended maintenance tasks" in maintain_plan_output
    assert "journalctl --vacuum-size=200M" in maintain_plan_output
    assert "Use --execute to run the available tasks now." in maintain_plan_output
    assert runner_instances[-1].use_sudo is root_enabled

    maintain_exec_output = invoke(["cadmu", "maintain", "--execute", "--sudo"])
    assert "journal: success (sudo)" in maintain_exec_output
    assert "pip-cache-info: success" in maintain_exec_output
    assert runner_instances[-1].use_sudo is True

    update_plan_output = invoke(["cadmu", "update"])
    assert "Planned update steps" in update_plan_output
    assert "Refresh repositories" in update_plan_output
    assert "Use --execute to run the update steps in order." in update_plan_output
    assert runner_instances[-1].use_sudo is root_enabled

    update_exec_output = invoke(["cadmu", "update", "--execute", "--sudo"])
    assert "Refresh repositories: success with sudo (pacman -Sy)" in update_exec_output
    assert "Upgrade packages: success with sudo (pacman -Su)" in update_exec_output
    assert runner_instances[-1].use_sudo is True

    arch_output = invoke([
        "cadmu",
        "arch",
        "--pacman",
        "--explicit-installed",
        "--recommendations",
        "--limit",
        "1",
    ])
    assert "PACKAGE TABLE" in arch_output
    assert "Oldest explicit installs" in arch_output
    assert "- python (3.13.0) • 450 days old • Tier-1 (Extra)" in arch_output
    assert runner_instances[-1].use_sudo is root_enabled

    assert len(runner_instances) == 10
