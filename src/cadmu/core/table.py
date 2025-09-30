from __future__ import annotations

import textwrap
from typing import Dict, List, Sequence


def render_table(headers: Sequence[str], rows: Sequence[Sequence[str]], *, max_widths: Dict[str, int] | None = None) -> str:
    if not headers:
        return ""
    max_widths = max_widths or {}
    wrapped_rows: List[List[List[str]]] = []
    col_widths = {header: len(header) for header in headers}

    for row in rows:
        wrapped_row: List[List[str]] = []
        for header, cell in zip(headers, row, strict=False):
            cell_text = cell or ""
            width = max_widths.get(header)
            if width:
                wrapped = textwrap.wrap(cell_text, width=width, break_long_words=False, drop_whitespace=False) or [""]
            else:
                wrapped = cell_text.splitlines() or [""]
            wrapped_row.append(wrapped)
            longest_line = max(len(line) for line in wrapped)
            if longest_line > col_widths[header]:
                col_widths[header] = longest_line
        wrapped_rows.append(wrapped_row)

    # Build horizontal separator
    sep_parts = ["+" + "-" * (col_widths[header] + 2) for header in headers]
    separator = "+".join(part for part in sep_parts) + "+"

    lines: List[str] = [separator]
    header_cells = [f" {header.ljust(col_widths[header])} " for header in headers]
    lines.append("|" + "|".join(header_cells) + "|")
    lines.append(separator)

    for wrapped_row in wrapped_rows:
        max_lines = max(len(col) for col in wrapped_row)
        for i in range(max_lines):
            line_cells = []
            for header, column in zip(headers, wrapped_row, strict=False):
                text = column[i] if i < len(column) else ""
                line_cells.append(f" {text.ljust(col_widths[header])} ")
            lines.append("|" + "|".join(line_cells) + "|")
        lines.append(separator)
    return "\n".join(lines)
