from __future__ import annotations

import sys
from datetime import datetime, timezone

import pytest

from cadmu.core.runner import CommandResult, CommandSpec
from cadmu.modules.arch import pacman as arch_pacman
from cadmu.modules.cleaning.base import CleanupAction


class DummyRunner:
    def __init__(self, use_sudo: bool = False):
        self.use_sudo = use_sudo

    def execute(self, spec: CommandSpec) -> CommandResult:  # pragma: no cover - not invoked in patched paths
        return CommandResult(spec=spec, stdout="", stderr="", exit_code=0, skipped=True, reason="dummy")


@pytest.fixture(autouse=True)
def reset_argv():
    original = list(sys.argv)
    yield
    sys.argv[:] = original


def test_cli_arch_command(monkeypatch, capsys):
    pkg = arch_pacman.PackageInfo(
        name="python",
        version="3.12.1-1",
        description="High-level language",
        install_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
        depends=["expat", "gdbm"],
        optional_deps=["sqlite"],
        repo="extra",
        is_foreign=False,
    )

    monkeypatch.setattr("cadmu.cli.CommandRunner", lambda use_sudo=False: DummyRunner(use_sudo))
    monkeypatch.setattr("cadmu.cli.arch_pacman.collect_explicit_infos", lambda runner: [pkg])
    monkeypatch.setattr(
        "cadmu.cli.arch_pacman.build_explicit_package_table",
        lambda runner, include_recommendations, limit, infos: "TABLE",  # noqa: ARG001
    )
    monkeypatch.setattr("cadmu.cli.arch_pacman.top_oldest_packages", lambda infos, limit=5: infos)

    sys.argv = ["cadmu", "arch", "--pacman", "--explicit-installed", "--recommendations"]

    from cadmu import cli  # Imported late to honour monkeypatching for CommandRunner

    cli.main()
    output = capsys.readouterr().out
    assert "TABLE" in output
    assert "python" in output or "Oldest explicit installs" in output


def test_cli_clean_plan(monkeypatch, capsys):
    actions = [
        CleanupAction(identifier="pip-cache", description="Purge pip cache", command=["pip", "cache", "purge"]),
        CleanupAction(identifier="npm-cache", description="Clean npm cache", command=["npm", "cache", "clean", "--force"], risk="medium"),
    ]
    monkeypatch.setattr("cadmu.cli.planned_actions", lambda options: actions)
    monkeypatch.setattr("cadmu.cli.CommandRunner", lambda use_sudo=False: DummyRunner(use_sudo))

    sys.argv = ["cadmu", "clean"]
    from cadmu import cli

    cli.main()
    output = capsys.readouterr().out
    assert "Cleanup plan" in output
    assert "pip cache" in output
    assert "Use --execute" in output
