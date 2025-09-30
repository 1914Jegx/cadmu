from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Sequence

from cadmu.core.runner import CommandRunner, CommandSpec
from cadmu.core.table import render_table

CHUNK_SIZE = 40


@dataclass(slots=True)
class PackageInfo:
    name: str
    version: str
    description: str
    install_date: datetime | None
    depends: List[str]
    optional_deps: List[str]
    repo: str | None
    is_foreign: bool

    @property
    def dependency_count(self) -> int:
        return len(self.depends)

    @property
    def age_days(self) -> int | None:
        if not self.install_date:
            return None
        delta = datetime.now(timezone.utc) - self.install_date
        return max(0, delta.days)


class PacmanDataError(RuntimeError):
    pass


def get_explicit_packages(runner: CommandRunner) -> List[str]:
    spec = CommandSpec(label="pacman -Qet", command=["pacman", "-Qet"], allow_missing=False)
    result = runner.execute(spec)
    if result.skipped:
        raise PacmanDataError(f"pacman unavailable: {result.reason}")
    if result.exit_code != 0:
        raise PacmanDataError(result.stderr or "pacman -Qet failed")
    packages = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        parts = line.split()
        packages.append(parts[0])
    return packages


def _chunked(seq: Sequence[str], size: int) -> Iterable[List[str]]:
    for i in range(0, len(seq), size):
        yield list(seq[i : i + size])


def _parse_pacman_query(output: str) -> List[Dict[str, str]]:
    records: List[Dict[str, str]] = []
    current: Dict[str, str] = {}
    current_key: str | None = None
    for line in output.splitlines():
        if not line.strip():
            if current:
                records.append(current)
                current = {}
                current_key = None
            continue
        if line.startswith(" ") and current_key:
            current[current_key] += " \n" + line.strip()
            continue
        if ":" in line:
            key, value = line.split(":", 1)
            current_key = key.strip()
            current[current_key] = value.strip()
    if current:
        records.append(current)
    return records


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    clean = value.replace("GMT", "UTC")
    for fmt in (
        "%a %d %b %Y %I:%M:%S %p %z",
        "%a %d %b %Y %H:%M:%S %z",
        "%a %d %b %Y %I:%M:%S %p",
    ):
        try:
            dt = datetime.strptime(clean, fmt)
            if not dt.tzinfo:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            continue
    return None


def _split_list(value: str | None) -> List[str]:
    if not value or value.lower() == "none":
        return []
    items: List[str] = []
    for part in value.split("  "):
        part = part.strip()
        if not part:
            continue
        items.extend(p.strip() for p in part.split("  ") if p.strip())
    return [item for item in (p.replace("\n", " ") for p in items) if item and item.lower() != "none"]


def get_package_infos(runner: CommandRunner, packages: Sequence[str]) -> List[PackageInfo]:
    infos: List[PackageInfo] = []
    repo_map = _get_repository_map(runner, packages)
    foreign_packages = set(_get_foreign_packages(runner))
    for chunk in _chunked(list(packages), CHUNK_SIZE):
        spec = CommandSpec(label="pacman -Qi", command=["pacman", "-Qi", *chunk], allow_missing=False)
        result = runner.execute(spec)
        if result.skipped or result.exit_code != 0:
            raise PacmanDataError(result.stderr or f"pacman -Qi failed for chunk {chunk}")
        for record in _parse_pacman_query(result.stdout):
            name = record.get("Name", "")
            infos.append(
                PackageInfo(
                    name=name,
                    version=record.get("Version", ""),
                    description=record.get("Description", ""),
                    install_date=_parse_date(record.get("Install Date")),
                    depends=_split_list(record.get("Depends On")),
                    optional_deps=_split_list(record.get("Optional Deps")),
                    repo=repo_map.get(name),
                    is_foreign=name in foreign_packages,
                )
            )
    infos.sort(key=lambda info: info.name)
    return infos


def _get_repository_map(runner: CommandRunner, packages: Sequence[str]) -> Dict[str, str]:
    repo_map: Dict[str, str] = {}
    for chunk in _chunked(list(packages), CHUNK_SIZE):
        spec = CommandSpec(label="pacman -Si", command=["pacman", "-Si", *chunk], allow_missing=True)
        result = runner.execute(spec)
        if result.skipped or result.exit_code != 0:
            continue
        for record in _parse_pacman_query(result.stdout):
            name = record.get("Name")
            repo = record.get("Repository")
            if name and repo:
                repo_map[name] = repo
    return repo_map


def _get_foreign_packages(runner: CommandRunner) -> List[str]:
    spec = CommandSpec(label="pacman -Qm", command=["pacman", "-Qm"], allow_missing=True)
    result = runner.execute(spec)
    if result.skipped or result.exit_code != 0:
        return []
    foreign: List[str] = []
    for line in result.stdout.splitlines():
        if line.strip():
            foreign.append(line.split()[0])
    return foreign


def classify_stability(info: PackageInfo) -> str:
    if info.is_foreign:
        return "AUR/External"
    repo = (info.repo or "").lower()
    if repo == "core":
        return "Tier-0 (Core)"
    if repo == "extra":
        return "Tier-1 (Extra)"
    if repo == "community" or repo.startswith("community"):
        return "Community"
    if not repo:
        return "Unknown"
    return repo.capitalize()


def classify_difficulty(info: PackageInfo) -> str:
    deps = info.dependency_count
    if deps <= 2:
        return "Easy to replace"
    if deps <= 6:
        return "Moderate complexity"
    if deps <= 15:
        return "High impact"
    return "Critical core dependency"


def general_recommendation(info: PackageInfo) -> str:
    stability = classify_stability(info)
    if stability.startswith("Tier-0"):
        return "Retain (system critical)"
    if stability.startswith("Tier-1"):
        return "Keep updated"
    if stability == "Community":
        return "Monitor maintainer updates"
    if stability == "AUR/External":
        return "Verify upstream health"
    return "Review periodically"


def difficulty_recommendation(info: PackageInfo) -> str:
    difficulty = classify_difficulty(info)
    if difficulty == "Easy to replace":
        return "Low-risk removal"
    if difficulty == "Moderate complexity":
        return "Plan short maintenance window"
    if difficulty == "High impact":
        return "Coordinate before removal"
    return "Treat as cornerstone"


def age_label(info: PackageInfo) -> str:
    days = info.age_days
    if days is None:
        return "Unknown"
    if days < 30:
        return "New (<30d)"
    if days < 180:
        return "Recent (<6mo)"
    if days < 365:
        return "Established (<1y)"
    return f"Legacy ({math.floor(days / 365)}y)"


def collect_explicit_infos(runner: CommandRunner) -> List[PackageInfo]:
    packages = get_explicit_packages(runner)
    if not packages:
        return []
    return get_package_infos(runner, packages)


def build_explicit_package_table(
    runner: CommandRunner,
    *,
    include_recommendations: bool = False,
    limit: int | None = None,
    infos: List[PackageInfo] | None = None,
) -> str:
    infos = infos if infos is not None else collect_explicit_infos(runner)
    if not infos:
        return "No explicitly installed packages found."
    if limit:
        infos = infos[:limit]

    headers = ["Package", "Version", "Description"]
    if include_recommendations:
        headers.extend(["General", "Difficulty", "Stability", "Age"])
    rows: List[List[str]] = []
    for info in infos:
        row = [info.name, info.version, info.description or "(no description)"]
        if include_recommendations:
            row.extend([
                general_recommendation(info),
                difficulty_recommendation(info),
                classify_stability(info),
                age_label(info),
            ])
        rows.append(row)
    return render_table(headers, rows, max_widths={"Description": 50})


def top_oldest_packages(infos: Sequence[PackageInfo], *, limit: int = 5) -> List[PackageInfo]:
    aged = [info for info in infos if info.age_days is not None]
    aged.sort(key=lambda info: info.age_days or 0, reverse=True)
    return aged[:limit]
