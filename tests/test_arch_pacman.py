from __future__ import annotations

import pytest

from cadmu.core.runner import CommandResult, CommandSpec
from cadmu.modules.arch import pacman


class StubRunner:
    """Minimal CommandRunner-compatible stub for testing."""

    def __init__(self, responses):
        self.responses = responses

    def execute(self, spec: CommandSpec) -> CommandResult:
        key = tuple(spec.command) if isinstance(spec.command, list) else spec.command
        payload = self.responses.get(key)
        if payload is None:
            return CommandResult(spec=spec, stdout="", stderr="", exit_code=1, skipped=True, reason="stub")
        return CommandResult(
            spec=spec,
            stdout=payload.get("stdout", ""),
            stderr=payload.get("stderr", ""),
            exit_code=payload.get("exit_code", 0),
            skipped=payload.get("skipped", False),
            reason=payload.get("reason"),
        )


@pytest.fixture()
def sample_runner():
    qi_output = """Name            : python\nVersion         : 3.12.1-1\nDescription     : High-level scripting language\nDepends On      : expat  bzip2  gdbm  util-linux\nOptional Deps   : sqlite: database support\nInstall Date    : Mon 01 Jan 2024 10:00:00 AM -0500\n\nName            : aurhelper\nVersion         : 1.0.0-1\nDescription     : Example AUR package\nDepends On      : base  git\nOptional Deps   : None\nInstall Date    : Mon 01 Jan 2023 09:00:00 AM -0500\n"""

    si_output = """Repository      : extra\nName            : python\nVersion         : 3.12.1-1\n\n"""

    responses = {
        ("pacman", "-Qet"): {"stdout": "python 3.12.1-1\naurhelper 1.0.0-1\n"},
        ("pacman", "-Qi", "python", "aurhelper"): {"stdout": qi_output},
        ("pacman", "-Si", "python", "aurhelper"): {"stdout": si_output},
        ("pacman", "-Qm"): {"stdout": "aurhelper 1.0.0-1\n"},
    }
    return StubRunner(responses)


def test_collect_explicit_infos(sample_runner):
    infos = pacman.collect_explicit_infos(sample_runner)  # type: ignore[arg-type]
    assert len(infos) == 2
    python_info = next(info for info in infos if info.name == "python")
    assert python_info.repo == "extra"
    assert python_info.dependency_count == 4
    assert python_info.is_foreign is False
    assert python_info.install_date.tzinfo is not None

    aur_info = next(info for info in infos if info.name == "aurhelper")
    assert aur_info.is_foreign is True
    assert pacman.classify_stability(aur_info) == "AUR/External"


def test_build_explicit_package_table(sample_runner):
    infos = pacman.collect_explicit_infos(sample_runner)  # type: ignore[arg-type]
    table = pacman.build_explicit_package_table(sample_runner, include_recommendations=True, infos=infos)  # type: ignore[arg-type]
    assert "python" in table
    assert "aurhelper" in table
    assert "Retain" in table or "Keep" in table
    assert "AUR/External" in table


def test_top_oldest_packages(sample_runner):
    infos = pacman.collect_explicit_infos(sample_runner)  # type: ignore[arg-type]
    oldest = pacman.top_oldest_packages(infos, limit=1)
    assert oldest[0].name == "aurhelper"
    # Age label should treat aurhelper as legacy (>1 year)
    assert pacman.age_label(oldest[0]).startswith("Legacy")
