from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator, Sequence


class ReportWriter:
    """Helper for structured diagnostic reports."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._fh = path.open("w", encoding="utf-8")

    def write_header(self, *, host: str, effective_user: str, owner: str) -> None:
        lines = [
            "System Diagnostic Report",
            f"Generated: {datetime.now().isoformat(timespec='seconds')}",
            f"Host: {host}",
            f"Effective user: {effective_user}",
            f"Report owner: {owner}",
            f"Output file: {self.path}",
            "",
        ]
        self._fh.write("\n".join(lines))

    def section(self, title: str) -> None:
        self._fh.write(f"===== {title} =====\n\n")
        self._fh.flush()

    def subsection(self, title: str) -> None:
        self._fh.write(f"--- {title} ---\n")
        self._fh.flush()

    def write_command(self, command: Sequence[str] | str, output: str) -> None:
        display = command if isinstance(command, str) else " ".join(command)
        self._fh.write(f"# {display}\n{output}\n\n")
        self._fh.flush()

    def note(self, message: str) -> None:
        self._fh.write(f"{message}\n")
        self._fh.flush()

    def close(self) -> None:
        self._fh.close()

    def __enter__(self) -> "ReportWriter":  # pragma: no cover - simple passthrough
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - close on exit
        self.close()


@contextmanager
def report_writer(path: Path, *, host: str, effective_user: str, owner: str) -> Iterator[ReportWriter]:
    writer = ReportWriter(path)
    try:
        writer.write_header(host=host, effective_user=effective_user, owner=owner)
        yield writer
    finally:
        writer.close()
