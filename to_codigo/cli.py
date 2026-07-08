"""CLI presentation layer for to-codigo.

This module contains all Rich-based rendering functions:
- ``show_banner()``: renders the ASCII banner + version.
- ``show_results_table()``: Rich table with per-language summary.
- ``show_todos_table()``: Rich table with TODO/FIXME/HACK markers.
- ``show_top_files_table()``: Rich table with top N files by LOC.
- ``show_diff_table()``: Rich table with diff results.
- ``show_error()``: Rich error panel with hint.
- ``show_warning()``: Rich warning panel.
- ``show_help_examples()``: formatted examples section.
- ``create_progress_bar()``: configured Rich Progress.
- ``show_success()``: success panel.

All Rich imports are centralized here to keep the CLI feeling alive.
"""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
)
from rich.table import Table
from rich.text import Text
from rich import box

from to_codigo.assets.banner import BANNER, VERSION, TAGLINE_ES, TAGLINE_EN
from to_codigo.core.models import FileInfo, TodoItem

console = Console()

# Marker colours for the TODO table.
MARKER_STYLES: dict[str, str] = {
    "TODO": "bold yellow",
    "FIXME": "bold red",
    "HACK": "bold orange3",
    "XXX": "bold orange3",
    "BUG": "bold red",
    "NOTE": "bold blue",
}


def show_banner(console: Console | None = None) -> None:
    """Render the startup ASCII banner with version and tagline.

    Uses a Rich Panel with a cyan border to frame the banner.
    """
    c = console or Console()

    # Build the banner text with gradient-like coloring (cyan to green).
    banner_text = Text()
    lines = BANNER.strip("\n").split("\n")
    for line in lines:
        banner_text.append(line + "\n", style="bold cyan")

    # Add version and tagline.
    banner_text.append(f"\n  v{VERSION}", style="bold green")
    banner_text.append(f"  -  {TAGLINE_ES}\n", style="dim white")
    banner_text.append(f"  Code Analyzer & Inventory Tool\n", style="dim italic white")

    c.print()
    c.print(Panel(
        banner_text,
        border_style="cyan",
        padding=(1, 2),
        expand=False,
    ))
    c.print()


def show_results_table(
    stats: dict[str, Any],
    total_files: int,
    elapsed: float,
    console: Console | None = None,
    skipped_binary: int = 0,
) -> None:
    """Render a Rich table with per-language results.

    Columns: Lenguaje | Archivos | Lineas Codigo | Lineas Comentario | % del Total
    Plus TODO and FIXME count columns.

    Args:
        stats: Dict mapping language name to LanguageStats.
        total_files: Total number of files scanned.
        elapsed: Elapsed time in seconds.
        skipped_binary: Number of binary files skipped during scan.
    """
    c = console or Console()

    if not stats:
        c.print("[yellow]No hay datos para mostrar.[/]")
        return

    total_code = sum(s.total_code_lines for s in stats.values())
    total_comment = sum(s.total_comment_lines for s in stats.values())
    total_blank = sum(s.total_blank_lines for s in stats.values())
    total_lines = sum(s.total_lines for s in stats.values())
    total_todos = sum(s.total_todos for s in stats.values())
    total_fixmes = sum(s.total_fixmes for s in stats.values())

    sorted_stats = sorted(stats.items(), key=lambda kv: kv[1].total_code_lines, reverse=True)
    max_code = sorted_stats[0][1].total_code_lines if sorted_stats else 0
    min_code = sorted_stats[-1][1].total_code_lines if sorted_stats else 0

    table = Table(
        title="[bold cyan]Resumen por Lenguaje[/]",
        show_lines=False,
        box=box.ROUNDED,
        title_style="bold cyan",
    )
    table.add_column("Lenguaje", style="bold white", min_width=16)
    table.add_column("Archivos", justify="right", style="cyan")
    table.add_column("Lineas Codigo", justify="right")
    table.add_column("Lineas Comentario", justify="right", style="yellow")
    table.add_column("Lineas Blanco", justify="right", style="dim")
    table.add_column("Total", justify="right")
    table.add_column("% Codigo", justify="right")
    table.add_column("TODOs", justify="right", style="yellow")
    table.add_column("FIXMEs", justify="right", style="red")

    for lang, data in sorted_stats:
        pct = (data.total_code_lines / total_code * 100) if total_code > 0 else 0

        # Color-code based on relative position.
        if data.total_code_lines == max_code:
            code_style = "bold green"
        elif data.total_code_lines == min_code:
            code_style = "dim"
        else:
            code_style = "white"

        table.add_row(
            lang,
            str(data.files),
            Text(f"{data.total_code_lines:,}", style=code_style),
            f"{data.total_comment_lines:,}",
            f"{data.total_blank_lines:,}",
            f"{data.total_lines:,}",
            f"{pct:.1f}%",
            str(data.total_todos),
            str(data.total_fixmes),
        )

    c.print()
    c.print(table)

    # Summary line below the table.
    c.print()
    summary_parts = [
        f"  [bold green]Total:[/] {total_files} archivos  "
        f"[green]{total_code:,}[/] codigo  "
        f"[yellow]{total_comment:,}[/] comentarios  "
        f"[dim]{total_blank:,}[/] blanco  "
        f"[bold]{total_lines:,}[/] lineas  "
        f"[yellow]{total_todos}[/] TODOs  "
        f"[red]{total_fixmes}[/] FIXMEs  "
        f"[cyan]{elapsed:.2f}s[/]"
    ]
    if skipped_binary > 0:
        summary_parts.append(
            f"\n  [dim italic]{skipped_binary} archivos binarios omitidos[/]"
        )
    c.print("".join(summary_parts))
    c.print()


def show_todos_table(
    todos: list[TodoItem],
    console: Console | None = None,
) -> None:
    """Render a Rich table with TODO/FIXME/HACK/NOTE markers.

    Columns: File | Line | Type (colored) | Text
    """
    c = console or Console()

    if not todos:
        c.print("\n  [green]No TODO/FIXME/HACK markers found. Clean![/]\n")
        return

    table = Table(
        title="[bold orange3]Tech Debt - TODOs / FIXMEs / HACKs[/]",
        show_lines=False,
        box=box.ROUNDED,
        title_style="bold orange3",
    )
    table.add_column("File", style="cyan", min_width=30)
    table.add_column("Line", justify="right", style="dim")
    table.add_column("Type", justify="center")
    table.add_column("Text", style="white")

    for item in sorted(todos, key=lambda t: (t.filepath, t.line_number)):
        style = MARKER_STYLES.get(item.marker, "white")
        table.add_row(
            Text(item.filepath, style="cyan"),
            str(item.line_number),
            Text(item.marker, style=style),
            Text(item.text[:120]),
        )

    c.print()
    c.print(table)
    c.print()


def show_top_files_table(
    files: list[FileInfo],
    top_n: int,
    console: Console | None = None,
) -> None:
    """Render a Rich table with the top N files by LOC.

    Args:
        files: All scanned files.
        top_n: Number of top files to show.
    """
    c = console or Console()

    top = sorted(files, key=lambda f: f.code_lines, reverse=True)[:top_n]

    if not top:
        return

    table = Table(
        title=f"[bold green]Top {top_n} Files by LOC[/]",
        show_lines=False,
        box=box.ROUNDED,
        title_style="bold green",
    )
    table.add_column("#", justify="right", style="dim", width=4)
    table.add_column("File", style="white", min_width=30)
    table.add_column("Language", style="cyan")
    table.add_column("LOC", justify="right", style="green")
    table.add_column("Comments", justify="right", style="yellow")
    table.add_column("Total", justify="right")

    for i, info in enumerate(top, 1):
        table.add_row(
            str(i),
            info.filename,
            info.language,
            f"{info.code_lines:,}",
            f"{info.comment_lines:,}",
            f"{info.total_lines:,}",
        )

    c.print()
    c.print(table)
    c.print()


def show_diff_table(
    diff: Any,
    console: Console | None = None,
) -> None:
    """Render a Rich table with diff results.

    Shows LOC changes by language (green for growth, red for shrink),
    plus added/removed/modified file counts.

    Args:
        diff: A :class:`~to_codigo.core.differ.DiffResult`.
    """
    c = console or Console()

    table = Table(
        title="[bold magenta]Diff Report[/]",
        show_lines=False,
        box=box.ROUNDED,
        title_style="bold magenta",
    )
    table.add_column("Language", style="white", min_width=16)
    table.add_column("LOC Change", justify="right")

    for lang, delta in sorted(
        diff.loc_changes_by_language.items(),
        key=lambda kv: kv[1],
        reverse=True,
    ):
        if delta > 0:
            table.add_row(lang, Text(f"+{delta:,} ↑", style="bold green"))
        else:
            table.add_row(lang, Text(f"{delta:,} ↓", style="bold red"))

    c.print()
    c.print(table)

    # Summary
    c.print()
    c.print(
        f"  [green]+{len(diff.added_files)}[/] added  "
        f"[red]-{len(diff.removed_files)}[/] removed  "
        f"[yellow]~{len(diff.modified_files)}[/] modified  "
        f"[green]+{diff.new_todos}[/] new TODOs  "
        f"[red]-{diff.resolved_todos}[/] resolved TODOs"
    )
    c.print()


def show_error(message: str, hint: str = "", console: Console | None = None) -> None:
    """Render a Rich error panel with red border.

    Args:
        message: The error message.
        hint: Optional usage hint shown below the message.
    """
    c = console or Console()

    content = f"[bold red]ERROR[/]\n\n[white]{message}[/]"
    if hint:
        content += f"\n\n[dim]Sugerencia: {hint}[/]"

    c.print()
    c.print(Panel(
        content,
        border_style="red",
        title="[red]Error[/]",
        padding=(1, 2),
    ))
    c.print()


def show_warning(message: str, console: Console | None = None) -> None:
    """Render a Rich warning panel with yellow border.

    Args:
        message: The warning message.
    """
    c = console or Console()
    c.print(Panel(
        f"[yellow]{message}[/]",
        border_style="yellow",
        title="[yellow]Aviso[/]",
        padding=(1, 2),
    ))


def show_success(message: str, console: Console | None = None) -> None:
    """Render a success panel with green border."""
    c = console or Console()
    c.print(Panel(
        f"[green]{message}[/]",
        border_style="green",
        padding=(0, 2),
    ))


def create_progress_bar() -> Progress:
    """Create and return a configured Rich Progress bar.

    Includes: spinner, description, bar, percentage, time remaining.
    """
    return Progress(
        SpinnerColumn(style="cyan"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(complete_style="green", finished_style="green"),
        TaskProgressColumn(),
        TextColumn("[dim]{task.completed}/{task.total} archivos[/]"),
        TimeRemainingColumn(),
        console=console,
    )


def show_help_examples(console: Console | None = None) -> None:
    """Render formatted examples section for --help output."""
    c = console or Console()

    c.print()
    c.print("[bold cyan]Ejemplos / Examples:[/]")
    c.print()
    c.print("  [dim]# Escanear un directorio (reporte CSV por defecto)[/]")
    c.print("  [green]$[/] to-codigo [blue]./src[/]")
    c.print()
    c.print("  [dim]# Exportar a Excel o JSON[/]")
    c.print("  [green]$[/] to-codigo [blue]./src[/] [yellow]-o[/] reporte [yellow]--format[/] xlsx")
    c.print("  [green]$[/] to-codigo [blue]./src[/] [yellow]--format[/] json")
    c.print()
    c.print("  [dim]# HTML Dashboard o Markdown[/]")
    c.print("  [green]$[/] to-codigo [blue]./src[/] [yellow]--format[/] html")
    c.print("  [green]$[/] to-codigo [blue]./src[/] [yellow]--format[/] md")
    c.print()
    c.print("  [dim]# TODO tracking + Top 5 archivos[/]")
    c.print("  [green]$[/] to-codigo [blue]./src[/] [yellow]--todos[/] [yellow]--top[/] 5")
    c.print()
    c.print("  [dim]# Diff contra un reporte anterior[/]")
    c.print("  [green]$[/] to-codigo [blue]./src[/] [yellow]--diff[/] prev-report.json")
    c.print()
    c.print("  [dim]# Solo Python y TypeScript[/]")
    c.print("  [green]$[/] to-codigo [blue]./src[/] [yellow]--include-ext[/] .py .ts")
    c.print()
    c.print("  [dim]# Shell completion[/]")
    c.print("  [green]$[/] to-codigo [yellow]--completion[/] bash > /etc/bash_completion.d/to-codigo")
    c.print()
    c.print("  [dim]# Respetar .gitignore + modo verbose[/]")
    c.print("  [green]$[/] to-codigo [blue]./src[/] [yellow]--respect-gitignore[/] [yellow]--verbose[/]")
    c.print()
