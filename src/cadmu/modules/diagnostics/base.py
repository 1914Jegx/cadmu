from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence

from cadmu.core.runner import CommandRunner, CommandSpec
from cadmu.core.reporting import ReportWriter
from cadmu.core.system import supports_systemd
from cadmu.modules.diagnostics import dependencies


@dataclass(slots=True)
class DiagnosticsOptions:
    home: Path
    include_optional: bool = True
    include_arch: bool = True


def _cmd(
    label: str,
    command: Sequence[str] | str,
    *,
    sudo: bool = False,
    allow_missing: bool = True,
    shell: bool = False,
    env: dict[str, str] | None = None,
    optional: bool = False,
) -> CommandSpec:
    return CommandSpec(
        label=label,
        command=command,
        sudo=sudo,
        allow_missing=allow_missing,
        shell=shell,
        env=env,
        optional=optional,
    )


def _home_env(home: Path) -> dict[str, str]:
    return {"HOME": str(home)}


def _baseline_sections(options: DiagnosticsOptions) -> List[tuple[str, Iterable[CommandSpec]]]:
    env_home = _home_env(options.home)
    sections: List[tuple[str, Iterable[CommandSpec]]] = [
        (
            "Operating System Basics",
            [
                _cmd("uname", ["uname", "-a"]),
                _cmd("os-release", ["cat", "/etc/os-release"]),
                _cmd("hostnamectl", ["hostnamectl"], optional=True),
                _cmd("timedatectl", ["timedatectl"], allow_missing=True, optional=True),
                _cmd("uptime", ["uptime"]),
                _cmd("who", ["who", "-a"]),
                _cmd("last", ["last", "-n", "20"], allow_missing=True),
            ],
        ),
        (
            "Environment & Sessions",
            [
                _cmd("loginctl", ["loginctl", "list-sessions"], allow_missing=not supports_systemd()),
                _cmd("systemd-analyze", ["systemd-analyze"], allow_missing=not supports_systemd(), optional=True),
                _cmd("systemd-analyze blame", ["systemd-analyze", "blame"], allow_missing=not supports_systemd(), optional=True),
                _cmd("systemd-analyze critical-chain", ["systemd-analyze", "critical-chain"], allow_missing=not supports_systemd(), optional=True),
            ],
        ),
        (
            "Hardware Overview",
            [
                _cmd("lscpu", ["lscpu"], allow_missing=True),
                _cmd("lsusb", ["lsusb"], allow_missing=True, optional=True),
                _cmd("lspci", ["lspci", "-nnk"], allow_missing=True, optional=True),
                _cmd("dmidecode", ["dmidecode"], sudo=True, allow_missing=True, optional=True),
                _cmd("lsblk", ["lsblk", "-o", "NAME,FSTYPE,LABEL,UUID,SIZE,FSUSED,FSUSE%,MOUNTPOINT"]),
                _cmd("lsmem", ["lsmem"], allow_missing=True),
                _cmd("meminfo", ["cat", "/proc/meminfo"]),
                _cmd("sensors", ["sensors"], allow_missing=True),
            ],
        ),
        (
            "Kernel & Modules",
            [
                _cmd("cmdline", ["cat", "/proc/cmdline"]),
                _cmd("lsmod", ["lsmod"]),
                _cmd("dmesg tail", ["bash", "-lc", "dmesg | tail -n 200"], allow_missing=True, optional=True),
            ],
        ),
        (
            "Storage & Filesystems",
            [
                _cmd("df -hT", ["df", "-hT"]),
                _cmd("df -i", ["df", "-i"]),
                _cmd("mount", ["mount"]),
                _cmd("findmnt", ["findmnt", "-A"], allow_missing=True),
                _cmd("du home top", ["bash", "-lc", "du -xh $HOME | sort -h | tail"], allow_missing=True, env=env_home, optional=True),
                _cmd("dot dirs", ["bash", "-lc", "du -sh $HOME/.* 2>/dev/null | sort -hr"], allow_missing=True, env=env_home, optional=True),
                _cmd("home dirs", ["bash", "-lc", "du -sh $HOME/* 2>/dev/null | sort -hr"], allow_missing=True, env=env_home, optional=True),
            ],
        ),
        (
            "Processes & Resource Usage",
            [
                _cmd("top", ["bash", "-lc", "COLUMNS=200 top -b -n1 | head -n 40"], allow_missing=True, optional=True),
                _cmd("ps", ["ps", "aux", "--sort=-%mem"]),
                _cmd("ps threads", ["bash", "-lc", "ps -eLf | head -n 200"], allow_missing=True, optional=True),
                _cmd("iotop", ["iotop", "-b", "-n", "3"], sudo=True, allow_missing=True, optional=True),
                _cmd("lsof", ["bash", "-lc", "lsof -nP | head -n 200"], sudo=True, allow_missing=True, optional=True),
            ],
        ),
        (
            "Networking",
            [
                _cmd("ip addr", ["ip", "addr"]),
                _cmd("ip route", ["ip", "route"]),
                _cmd("ss", ["ss", "-tulpn"], sudo=True, allow_missing=True, optional=True),
                _cmd("nmcli", ["nmcli", "device", "status"], allow_missing=True, optional=True),
                _cmd("resolvectl", ["resolvectl", "status"], allow_missing=True, optional=True),
                _cmd("iptables", ["iptables", "-S"], sudo=True, allow_missing=True, optional=True),
                _cmd("nft", ["nft", "list", "ruleset"], sudo=True, allow_missing=True, optional=True),
                _cmd("hosts", ["cat", "/etc/hosts"]),
                _cmd("resolv.conf", ["cat", "/etc/resolv.conf"]),
            ],
        ),
        (
            "Security",
            [
                _cmd("selinux", ["sestatus"], allow_missing=True, optional=True),
                _cmd("apparmor", ["aa-status"], sudo=True, allow_missing=True, optional=True),
                _cmd("fail2ban", ["fail2ban-client", "status"], sudo=True, allow_missing=True, optional=True),
                _cmd("ufw", ["ufw", "status", "verbose"], sudo=True, allow_missing=True, optional=True),
                _cmd("audit log", ["journalctl", "-p", "3", "-xb"], sudo=True, allow_missing=True, optional=True),
            ],
        ),
        (
            "Logs",
            [
                _cmd("journal last boot", ["journalctl", "-b", "-1"], sudo=True, allow_missing=True, optional=True),
                _cmd("journal last hour", ["journalctl", "--since", "-1 hour"], sudo=True, allow_missing=True, optional=True),
                _cmd("syslog tail", ["tail", "-n", "400", "/var/log/syslog"], sudo=True, allow_missing=True, optional=True),
                _cmd("messages tail", ["tail", "-n", "400", "/var/log/messages"], sudo=True, allow_missing=True, optional=True),
            ],
        ),
        (
            "User & Auth",
            [
                _cmd("id", ["id"]),
                _cmd("passwd entries", ["getent", "passwd"]),
                _cmd("group entries", ["getent", "group"]),
                _cmd("lastlog", ["lastlog"]),
                _cmd("sudoers", ["cat", "/etc/sudoers"], sudo=True, optional=True),
                _cmd("sudoers.d", ["bash", "-lc", "ls -R /etc/sudoers.d 2>/dev/null"], sudo=True, allow_missing=True, optional=True),
            ],
        ),
        (
            "Software Inventory",
            [
                _cmd("python", ["python", "--version"], allow_missing=True),
                _cmd("pip list", ["pip", "list"], allow_missing=True, optional=True),
                _cmd("pipx list", ["pipx", "list"], allow_missing=True, optional=True),
                _cmd("node", ["node", "-v"], allow_missing=True, optional=True),
                _cmd("npm", ["npm", "list", "-g", "--depth=0"], allow_missing=True, optional=True),
                _cmd("pnpm", ["pnpm", "list", "-g", "--depth=1"], allow_missing=True, optional=True),
                _cmd("yarn", ["yarn", "global", "list"], allow_missing=True, optional=True),
                _cmd("go env", ["go", "env"], allow_missing=True, optional=True),
                _cmd("cargo", ["cargo", "install", "--list"], allow_missing=True, optional=True),
                _cmd("java", ["java", "-version"], allow_missing=True, optional=True),
            ],
        ),
    ]
    return sections


def run_diagnostics(writer: ReportWriter, runner: CommandRunner, options: DiagnosticsOptions, *, arch_sections: Iterable[tuple[str, Iterable[CommandSpec]]] | None = None) -> None:
    writer.section("Dependency Verification")
    writer.note(dependencies.summarise(dependencies.GENERAL_DEPENDENCIES))
    if options.include_arch:
        writer.note("")
        writer.note(dependencies.summarise(dependencies.ARCH_DEPENDENCIES))
    writer.note("")

    for section, commands in _baseline_sections(options):
        writer.section(section)
        _run_commands(writer, runner, commands, include_optional=options.include_optional)

    if options.include_arch and arch_sections:
        for section, commands in arch_sections:
            writer.section(section)
            _run_commands(writer, runner, commands, include_optional=options.include_optional)

    writer.section("Custom Notes")
    writer.note("Add additional manual observations below as needed.")


def _run_commands(
    writer: ReportWriter,
    runner: CommandRunner,
    commands: Iterable[CommandSpec],
    *,
    include_optional: bool,
) -> None:
    for spec in commands:
        if spec.optional and not include_optional:
            writer.write_command(spec.command, "(skipped optional command)")
            continue
        result = runner.execute(spec)
        if result.skipped:
            writer.write_command(spec.command, f"(skipped) {result.reason or ''}".strip())
            continue
        output_blocks = [result.stdout]
        if result.stderr:
            output_blocks.append(f"[stderr]\n{result.stderr}")
        writer.write_command(spec.command, "\n".join(block for block in output_blocks if block))
