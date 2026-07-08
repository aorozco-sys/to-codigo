"""Report generation -- Strategy pattern.

Each reporter implements the :class:`Reporter` interface. Callers select a
concrete reporter at runtime via the ``REPORTERS`` registry:

.. code-block:: python

   reporter_cls = REPORTERS["xlsx"]
   reporter_cls().generate(files, stats, "output.xlsx")
"""

from __future__ import annotations

import csv
import json
import logging
import math
import os
from abc import ABC, abstractmethod
from dataclasses import asdict
from datetime import datetime
from html import escape
from typing import Any

from to_codigo.core.models import FileInfo, LanguageStats, TodoItem

logger = logging.getLogger(__name__)

HEADERS: tuple[str, ...] = (
    "Ruta_Absoluta_Archivo",
    "Ruta_Relativa_Carpeta",
    "Nombre_Archivo",
    "Lenguaje_Programacion",
    "Tamano_Bytes",
    "Fecha_Modificacion",
    "Lineas_Totales",
    "Lineas_Codigo",
    "Lineas_Comentarios",
    "Lineas_Blanco",
    "TODOs",
    "FIXMEs",
)

SUMMARY_HEADERS: tuple[str, ...] = (
    "Lenguaje",
    "Archivos",
    "Lineas_Codigo_Total",
    "Lineas_Comentarios_Total",
    "Lineas_Blanco_Total",
    "Lineas_Totales",
    "TODOs",
    "FIXMEs",
)

# Colour palette for charts (cycle through these).
LANG_COLORS: tuple[str, ...] = (
    "#7dcfff", "#9ece6a", "#ff9e64", "#f7768e",
    "#7aa2f7", "#bb9af7", "#e0af68", "#73daca",
    "#c0caf5", "#b4f9f8", "#2ac3de", "#89ddff",
)


def _file_to_row(info: FileInfo) -> list[Any]:
    """Convert a :class:`FileInfo` to a list matching :data:`HEADERS`."""
    return [
        info.absolute_path,
        info.relative_path,
        info.filename,
        info.language,
        info.size_bytes,
        info.modified_at,
        info.total_lines,
        info.code_lines,
        info.comment_lines,
        info.blank_lines,
        info.todos,
        info.fixmes,
    ]


# ---------------------------------------------------------------------------
# Abstract strategy
# ---------------------------------------------------------------------------

class Reporter(ABC):
    """Abstract base class for all report strategies."""

    @abstractmethod
    def generate(
        self,
        files: list[FileInfo],
        stats: dict[str, LanguageStats],
        output_path: str,
    ) -> None:
        """Write the report to *output_path*.

        Args:
            files: List of per-file records.
            stats: Per-language aggregate statistics.
            output_path: Destination file path.
        """
        ...


# ---------------------------------------------------------------------------
# CSV strategy
# ---------------------------------------------------------------------------

class CSVReporter(Reporter):
    """Comma-separated values report (RFC 4180 compliant via :mod:`csv`)."""

    def generate(
        self,
        files: list[FileInfo],
        stats: dict[str, LanguageStats],
        output_path: str,
    ) -> None:
        with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(HEADERS)
            for info in files:
                writer.writerow(_file_to_row(info))

            writer.writerow([])
            writer.writerow(["Resumen por Lenguaje"])
            writer.writerow(SUMMARY_HEADERS)
            for lang, data in stats.items():
                writer.writerow([
                    lang,
                    data.files,
                    data.total_code_lines,
                    data.total_comment_lines,
                    data.total_blank_lines,
                    data.total_lines,
                    data.total_todos,
                    data.total_fixmes,
                ])
        logger.info("CSV report generated: %s", output_path)


# ---------------------------------------------------------------------------
# XLSX strategy
# ---------------------------------------------------------------------------

class XLSXReporter(Reporter):
    """Excel report with styled headers, auto-filter, frozen panes, and
    a colour-coded summary section.

    Requires the ``openpyxl`` package.
    """

    # Reasonable column widths (in Excel units).
    _COLUMN_WIDTHS: tuple[int, ...] = (
        60,  # absolute path
        35,  # relative path
        30,  # filename
        18,  # language
        14,  # size
        22,  # modified at
        14,  # total lines
        14,  # code lines
        16,  # comment lines
        14,  # blank lines
        10,  # TODOs
        10,  # FIXMEs
    )

    def generate(
        self,
        files: list[FileInfo],
        stats: dict[str, LanguageStats],
        output_path: str,
    ) -> None:
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment

        wb = Workbook()
        ws = wb.active
        ws.title = "to-codigo"

        # --- Styles ---
        header_font = Font(bold=True, color="FFFFFF", size=11)
        header_fill = PatternFill(start_color="2F5496", end_color="2F5496", fill_type="solid")
        summary_header_font = Font(bold=True, color="FFFFFF", size=11)
        summary_header_fill = PatternFill(start_color="C55A11", end_color="C55A11", fill_type="solid")
        summary_title_font = Font(bold=True, size=13, color="C55A11")

        # --- Header row ---
        for col, header in enumerate(HEADERS, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center")

        # --- Column widths ---
        from openpyxl.utils import get_column_letter
        for col, width in enumerate(self._COLUMN_WIDTHS, 1):
            ws.column_dimensions[get_column_letter(col)].width = width

        # --- Data rows ---
        for row_idx, info in enumerate(files, 2):
            for col, value in enumerate(_file_to_row(info), 1):
                ws.cell(row=row_idx, column=col, value=value)

        last_data_row = len(files) + 1

        # --- Auto-filter on header row ---
        if files:
            ws.auto_filter.ref = f"A1:{get_column_letter(len(HEADERS))}{last_data_row}"

        # --- Freeze top row ---
        ws.freeze_panes = "A2"

        # --- Summary section ---
        summary_start = last_data_row + 3  # gap row

        title_cell = ws.cell(row=summary_start, column=1, value="Resumen por Lenguaje")
        title_cell.font = summary_title_font

        summary_header_row = summary_start + 1
        for col, header in enumerate(SUMMARY_HEADERS, 1):
            cell = ws.cell(row=summary_header_row, column=col, value=header)
            cell.font = summary_header_font
            cell.fill = summary_header_fill
            cell.alignment = Alignment(horizontal="center")

        for offset, (lang, data) in enumerate(stats.items()):
            row = summary_header_row + 1 + offset
            ws.cell(row=row, column=1, value=lang)
            ws.cell(row=row, column=2, value=data.files)
            ws.cell(row=row, column=3, value=data.total_code_lines)
            ws.cell(row=row, column=4, value=data.total_comment_lines)
            ws.cell(row=row, column=5, value=data.total_blank_lines)
            ws.cell(row=row, column=6, value=data.total_lines)
            ws.cell(row=row, column=7, value=data.total_todos)
            ws.cell(row=row, column=8, value=data.total_fixmes)

        wb.save(output_path)
        logger.info("XLSX report generated: %s", output_path)


# ---------------------------------------------------------------------------
# JSON strategy
# ---------------------------------------------------------------------------

class JSONReporter(Reporter):
    """Structured JSON report with file details and per-language summary."""

    def generate(
        self,
        files: list[FileInfo],
        stats: dict[str, LanguageStats],
        output_path: str,
    ) -> None:
        payload: dict[str, Any] = {
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "files": [asdict(f) for f in files],
            "summary": {
                lang: {
                    "files": s.files,
                    "total_code_lines": s.total_code_lines,
                    "total_comment_lines": s.total_comment_lines,
                    "total_blank_lines": s.total_blank_lines,
                    "total_lines": s.total_lines,
                    "total_todos": s.total_todos,
                    "total_fixmes": s.total_fixmes,
                    "total_hacks": s.total_hacks,
                    "total_notes": s.total_notes,
                }
                for lang, s in stats.items()
            },
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        logger.info("JSON report generated: %s", output_path)


# ---------------------------------------------------------------------------
# Markdown strategy
# ---------------------------------------------------------------------------

class MarkdownReporter(Reporter):
    """Markdown report with summary tables, top files, and tech debt section."""

    def generate(
        self,
        files: list[FileInfo],
        stats: dict[str, LanguageStats],
        output_path: str,
    ) -> None:
        from to_codigo.assets.banner import BANNER, VERSION

        total_code = sum(s.total_code_lines for s in stats.values())
        total_comment = sum(s.total_comment_lines for s in stats.values())
        total_blank = sum(s.total_blank_lines for s in stats.values())
        total_lines = sum(s.total_lines for s in stats.values())
        total_todos = sum(s.total_todos for s in stats.values())
        total_fixmes = sum(s.total_fixmes for s in stats.values())

        lines: list[str] = []

        lines.append("# to-codigo Report\n")
        lines.append("```\n" + BANNER.strip("\n") + "\n```\n")
        lines.append(f"**v{VERSION}** - Code Analyzer & Inventory Tool\n")
        lines.append("---\n")

        # Summary table
        lines.append("## Summary\n")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Total Files | {len(files)} |")
        lines.append(f"| Total LOC | {total_code:,} |")
        lines.append(f"| Total Comments | {total_comment:,} |")
        lines.append(f"| Total Blank | {total_blank:,} |")
        lines.append(f"| Total Lines | {total_lines:,} |")
        lines.append(f"| TODOs | {total_todos} |")
        lines.append(f"| FIXMEs | {total_fixmes} |")
        lines.append("")

        # Per-language table
        lines.append("## Per-Language Breakdown\n")
        lines.append("| Language | Files | LOC | Comments | Blank | Total | TODOs | FIXMEs |")
        lines.append("|----------|-------|-----|----------|-------|-------|-------|--------|")
        sorted_stats = sorted(stats.items(), key=lambda kv: kv[1].total_code_lines, reverse=True)
        for lang, data in sorted_stats:
            lines.append(
                f"| {lang} | {data.files} | {data.total_code_lines:,} | "
                f"{data.total_comment_lines:,} | {data.total_blank_lines:,} | "
                f"{data.total_lines:,} | {data.total_todos} | {data.total_fixmes} |"
            )
        lines.append("")

        # Top 10 files
        top_files = sorted(files, key=lambda f: f.code_lines, reverse=True)[:10]
        if top_files:
            lines.append("## Top 10 Files by LOC\n")
            lines.append("| Rank | File | Language | LOC |")
            lines.append("|------|------|----------|-----|")
            for i, info in enumerate(top_files, 1):
                lines.append(f"| {i} | {info.filename} | {info.language} | {info.code_lines:,} |")
            lines.append("")

        # Tech debt
        debt_files = [f for f in files if f.todos > 0 or f.fixmes > 0 or f.hacks > 0]
        if debt_files:
            lines.append("## Tech Debt\n")
            lines.append("| File | TODOs | FIXMEs | HACKs |")
            lines.append("|------|-------|--------|-------|")
            for info in debt_files:
                lines.append(
                    f"| {info.filename} | {info.todos} | {info.fixmes} | {info.hacks} |"
                )
            lines.append("")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines.append(f"\n---\n*Generated: {timestamp}*\n")

        with open(output_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        logger.info("Markdown report generated: %s", output_path)


# ---------------------------------------------------------------------------
# HTML strategy
# ---------------------------------------------------------------------------

class HTMLReporter(Reporter):
    """Self-contained HTML dashboard with charts, tables, and tech debt.

    Reads a template file, fills in placeholders with real data, and writes
    the output. Fully offline (no external CDNs or resources).
    """

    _TEMPLATE_PATH = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "templates",
        "dashboard.html",
    )

    def generate(
        self,
        files: list[FileInfo],
        stats: dict[str, LanguageStats],
        output_path: str,
    ) -> None:
        from to_codigo.assets.banner import BANNER, VERSION

        with open(self._TEMPLATE_PATH, "r", encoding="utf-8") as f:
            template = f.read()

        # --- Summary numbers ---
        total_code = sum(s.total_code_lines for s in stats.values())
        total_comment = sum(s.total_comment_lines for s in stats.values())

        # --- Sorted stats ---
        sorted_stats = sorted(
            stats.items(),
            key=lambda kv: kv[1].total_code_lines,
            reverse=True,
        )

        # --- Bar chart ---
        max_loc = max(
            (s.total_code_lines for _, s in sorted_stats),
            default=1,
        )
        if max_loc == 0:
            max_loc = 1

        bar_parts: list[str] = []
        for idx, (lang, data) in enumerate(sorted_stats):
            pct = (data.total_code_lines / max_loc) * 100
            color = LANG_COLORS[idx % len(LANG_COLORS)]
            bar_parts.append(
                f'<div class="bar-row">'
                f'<div class="bar-label">{escape(lang)}</div>'
                f'<div class="bar-track">'
                f'<div class="bar-fill" style="width:{pct:.1f}%;background:{color}"></div>'
                f'<div class="bar-value">{data.total_code_lines:,}</div>'
                f'</div></div>'
            )
        bar_html = "\n".join(bar_parts)

        # --- Pie chart (SVG) ---
        total_files = sum(s.files for _, s in sorted_stats)
        pie_svg = self._build_pie_svg(sorted_stats, total_files)
        pie_legend = self._build_pie_legend(sorted_stats, total_files)

        # --- Table rows ---
        table_rows: list[str] = []
        for info in sorted(files, key=lambda f: f.code_lines, reverse=True):
            table_rows.append(
                f"<tr>"
                f'<td data-val="{escape(info.filename)}">{escape(info.filename)}</td>'
                f'<td data-val="{escape(info.language)}"><span class="lang-badge" '
                f'style="background:#2a2e3f;color:#7dcfff">{escape(info.language)}</span></td>'
                f'<td data-val="{info.code_lines}">{info.code_lines:,}</td>'
                f'<td data-val="{info.comment_lines}">{info.comment_lines:,}</td>'
                f'<td data-val="{info.blank_lines}">{info.blank_lines:,}</td>'
                f'<td data-val="{info.total_lines}">{info.total_lines:,}</td>'
                f"</tr>"
            )
        table_html = "\n".join(table_rows)

        # --- Top 10 files ---
        top_files = sorted(files, key=lambda f: f.code_lines, reverse=True)[:10]
        top_parts: list[str] = []
        for i, info in enumerate(top_files, 1):
            top_parts.append(
                f'<div class="top-file">'
                f'<div class="top-rank">{i}</div>'
                f'<div class="top-info">'
                f'<div class="top-name">{escape(info.filename)}</div>'
                f'<div class="top-lang">{escape(info.language)} - {escape(info.relative_path)}</div>'
                f"</div>"
                f'<div class="top-loc">{info.code_lines:,} LOC</div>'
                f"</div>"
            )
        top_html = "\n".join(top_parts) if top_parts else '<div class="no-data">No files found</div>'

        # --- Tech debt ---
        all_todos: list[TodoItem] = []
        for info in files:
            if info.todos + info.fixmes + info.hacks + info.notes > 0:
                pass  # We don't have TodoItem list here; use counts
        debt_parts: list[str] = []
        debt_files = sorted(
            [f for f in files if f.todos + f.fixmes + f.hacks + f.notes > 0],
            key=lambda f: f.todos + f.fixmes + f.hacks + f.notes,
            reverse=True,
        )
        if debt_files:
            for info in debt_files:
                parts: list[str] = []
                if info.todos:
                    parts.append(f'<span class="debt-marker" style="background:#ff9e64">TODO: {info.todos}</span>')
                if info.fixmes:
                    parts.append(f'<span class="debt-marker" style="background:#f7768e">FIXME: {info.fixmes}</span>')
                if info.hacks:
                    parts.append(f'<span class="debt-marker" style="background:#e0af68">HACK: {info.hacks}</span>')
                if info.notes:
                    parts.append(f'<span class="debt-marker" style="background:#7aa2f7">NOTE: {info.notes}</span>')
                debt_parts.append(
                    f'<div class="debt-item">'
                    f'<div class="debt-header">'
                    f"{' '.join(parts)}"
                    f'<span class="debt-file">{escape(info.filename)}</span>'
                    f'<span class="debt-line">({info.relative_path})</span>'
                    f"</div>"
                    f"</div>"
                )
        debt_html = "\n".join(debt_parts) if debt_parts else '<div class="no-data">No TODOs, FIXMEs, or HACKs found. Clean codebase!</div>'

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # --- Fill template ---
        result = template
        replacements = {
            "{{BANNER}}": escape(BANNER.strip("\n")),
            "{{VERSION}}": VERSION,
            "{{TOTAL_FILES}}": str(len(files)),
            "{{TOTAL_LOC}}": f"{total_code:,}",
            "{{TOTAL_COMMENTS}}": f"{total_comment:,}",
            "{{LANGUAGES_COUNT}}": str(len(stats)),
            "{{BAR_CHART_HTML}}": bar_html,
            "{{PIE_CHART_SVG}}": pie_svg,
            "{{PIE_LEGEND_HTML}}": pie_legend,
            "{{TABLE_ROWS_HTML}}": table_html,
            "{{TOP_FILES_HTML}}": top_html,
            "{{TECH_DEBT_HTML}}": debt_html,
            "{{TIMESTAMP}}": timestamp,
        }
        for placeholder, value in replacements.items():
            result = result.replace(placeholder, value)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result)
        logger.info("HTML report generated: %s", output_path)

    @staticmethod
    def _build_pie_svg(
        sorted_stats: list[tuple[str, LanguageStats]],
        total_files: int,
    ) -> str:
        """Build an inline SVG pie chart with stroke-dasharray segments."""
        radius = 80
        circumference = 2 * math.pi * radius
        offset = 0

        segments: list[str] = []
        for idx, (lang, data) in enumerate(sorted_stats):
            if total_files == 0:
                break
            fraction = data.files / total_files
            length = fraction * circumference
            color = LANG_COLORS[idx % len(LANG_COLORS)]

            if length < 0.5:
                continue

            segments.append(
                f'<circle cx="100" cy="100" r="{radius}" fill="none" '
                f'stroke="{color}" stroke-width="30" '
                f'stroke-dasharray="{length:.2f} {circumference - length:.2f}" '
                f'stroke-dashoffset="{-offset:.2f}" '
                f'transform="rotate(-90 100 100)" />'
            )
            offset += length

        svg = (
            f'<svg width="200" height="200" viewBox="0 0 200 200" '
            f'xmlns="http://www.w3.org/2000/svg">'
        )
        # Background circle
        svg += (
            f'<circle cx="100" cy="100" r="{radius}" fill="none" '
            f'stroke="#2a2e3f" stroke-width="30" />'
        )
        svg += "".join(segments)
        svg += f'<text x="100" y="95" text-anchor="middle" fill="#a9b1d6" font-size="28" font-weight="bold">{total_files}</text>'
        svg += '<text x="100" y="115" text-anchor="middle" fill="#565f89" font-size="12">files</text>'
        svg += "</svg>"
        return svg

    @staticmethod
    def _build_pie_legend(
        sorted_stats: list[tuple[str, LanguageStats]],
        total_files: int,
    ) -> str:
        """Build the legend HTML for the pie chart."""
        parts: list[str] = []
        for idx, (lang, data) in enumerate(sorted_stats):
            color = LANG_COLORS[idx % len(LANG_COLORS)]
            pct = (data.files / total_files * 100) if total_files > 0 else 0
            parts.append(
                f'<div class="legend-item">'
                f'<div class="legend-color" style="background:{color}"></div>'
                f'<span class="legend-label">{escape(lang)}</span>'
                f'<span class="legend-value">{data.files} ({pct:.1f}%)</span>'
                f"</div>"
            )
        return "\n".join(parts)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

REPORTERS: dict[str, type[Reporter]] = {
    "csv": CSVReporter,
    "xlsx": XLSXReporter,
    "json": JSONReporter,
    "html": HTMLReporter,
    "md": MarkdownReporter,
}
