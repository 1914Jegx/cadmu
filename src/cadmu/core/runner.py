from __future__ import annotations

import shlex
import shutil
import subprocess
from dataclasses import dataclass
from typing import Mapping, MutableMapping, Sequence


@dataclass(slots=True)
class CommandSpec:
    label: str
    command: Sequence[str] | str
    allow_missing: bool = True
    check: bool = False
    shell: bool = False
    sudo: bool = False
    env: Mapping[str, str] | None = None
    timeout: int | None = None
    optional: bool = False


@dataclass(slots=True)
class CommandResult:
    spec: CommandSpec
    stdout: str
    stderr: str
    exit_code: int
    skipped: bool = False
    reason: str | None = None

    @property
    def ok(self) -> bool:
        return self.skipped or self.exit_code == 0


class CommandRunner:
    def __init__(self, *, use_sudo: bool = False) -> None:
        self.use_sudo = use_sudo

    def execute(self, spec: CommandSpec) -> CommandResult:
        command = spec.command
        env: MutableMapping[str, str] | None = None
        if spec.env:
            env = {**spec.env}

        if isinstance(command, Sequence) and not spec.shell:
            executable = command[0]
            if spec.sudo:
                if not self.use_sudo:
                    return CommandResult(
                        spec=spec,
                        stdout="",
                        stderr="",
                        exit_code=126,
                        skipped=True,
                        reason="sudo required but not enabled",
                    )
                command = ["sudo", *command]
            if shutil.which(executable) is None:
                if spec.allow_missing:
                    return CommandResult(
                        spec=spec,
                        stdout="",
                        stderr="",
                        exit_code=127,
                        skipped=True,
                        reason=f"Command '{executable}' not found",
                    )
                raise FileNotFoundError(f"Command '{executable}' not found")
        elif isinstance(command, str) and spec.sudo:
            if not self.use_sudo:
                return CommandResult(
                    spec=spec,
                    stdout="",
                    stderr="",
                    exit_code=126,
                    skipped=True,
                    reason="sudo required but not enabled",
                )
            command = f"sudo {command}"

        result = subprocess.run(
            command,
            shell=spec.shell or isinstance(command, str),
            env=env,
            capture_output=True,
            text=True,
            timeout=spec.timeout,
        )
        if spec.check:
            result.check_returncode()
        return CommandResult(
            spec=spec,
            stdout=result.stdout.strip(),
            stderr=result.stderr.strip(),
            exit_code=result.returncode,
        )

    @staticmethod
    def format_command(command: Sequence[str] | str) -> str:
        if isinstance(command, str):
            return command
        return " ".join(shlex.quote(part) for part in command)
