#!/usr/bin/env python3
"""CLI entry point for to-codigo.

Usage::

    python -m to_codigo /path/to/scan -o reporte --format xlsx
    python -m to_codigo . --format json --include-ext .py .ts --workers 8
    python -m to_codigo src/ --no-recursive --respect-gitignore --verbose
    python -m to_codigo . --todos --top 10
    python -m to_codigo . --format json -o /tmp/scan --diff /tmp/prev.json
    python -m to_codigo --completion bash
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import textwrap
import time

from rich.console import Console

from to_codigo.cli import (
    show_banner,
    show_results_table,
    show_todos_table,
    show_top_files_table,
    show_diff_table,
    show_error,
    show_warning,
    show_success,
    create_progress_bar,
    show_help_examples,
)
from to_codigo.assets.banner import VERSION
from to_codigo.core.scanner import scan_directory, compute_stats, _collect_files, _load_gitignore
from to_codigo.core.scanner import DEFAULT_EXCLUDE_DIRS, _process_file
from to_codigo.core.reporter import REPORTERS
from to_codigo.core.differ import diff_reports
from to_codigo.core.models import FileInfo

console = Console()


# ---------------------------------------------------------------------------
# Shell completion generators
# ---------------------------------------------------------------------------

def _generate_completion(shell: str) -> str:
    """Generate a shell completion script for *shell*.

    Uses argparse introspection on the parser's registered arguments.
    """
    if shell == "bash":
        return textwrap.dedent("""\
            _to_codigo_completions() {
                local cur prev opts
                COMPREPLY=()
                cur="${COMP_WORDS[COMP_CWORD]}"
                prev="${COMP_WORDS[COMP_CWORD-1]}"

                case "${prev}" in
                    --format)
                        COMPREPLY=($(compgen -W "csv xlsx json html md" -- ${cur}))
                        return 0
                        ;;
                    --completion)
                        COMPREPLY=($(compgen -W "bash zsh fish" -- ${cur}))
                        return 0
                        ;;
                esac

                if [[ ${cur} == --* ]]; then
                    opts="--output --format --exclude-dirs --exclude-ext --include-ext \
                          --no-recursive --respect-gitignore --workers --verbose \
                          --no-banner --version --todos --top --diff --completion --help"
                    COMPREPLY=($(compgen -W "${opts}" -- ${cur}))
                    return 0
                fi

                COMPREPLY=($(compgen -d -- ${cur}))
            }
            complete -F _to_codigo_completions to-codigo
        """)

    if shell == "zsh":
        return textwrap.dedent("""\
            #compdef to-codigo

            _to_codigo() {
                local -a commands opts formats
                formats=("csv" "xlsx" "json" "html" "md")
                opts=(
                    '--output[Output file base name]:filename'
                    '--format[Output format]:format:->formats'
                    '--exclude-dirs[Directories to exclude]:dir:_dirs'
                    '--exclude-ext[Extensions to exclude]:ext'
                    '--include-ext[Only scan these extensions]:ext'
                    '--no-recursive[Do not recurse]'
                    '--respect-gitignore[Respect .gitignore]'
                    '--workers[Number of parallel workers]:num'
                    '--verbose[Show warnings]'
                    '--no-banner[Hide banner]'
                    '--version[Show version]'
                    '--todos[Scan for TODO/FIXME markers]'
                    '--top[Show top N files by LOC]:num'
                    '--diff[Diff against previous report]:file:_files'
                    '--completion[Generate shell completion]:shell:(bash zsh fish)'
                )

                _arguments -C \\
                    '1:ruta_raiz:_dirs' \\
                    "${opts[@]}"

                case $state in
                    formats)
                        _describe 'format' formats
                        ;;
                esac
            }

            _to_codigo "$@"
        """)

    if shell == "fish":
        return textwrap.dedent("""\
            # Fish completions for to-codigo

            complete -c to-codigo -f -a '(__fish_complete_directories)' -d "Directory to scan"

            complete -c to-codigo -l output -d "Output file base name" -r
            complete -c to-codigo -l format -d "Output format" -x -a "csv xlsx json html md"
            complete -c to-codigo -l exclude-dirs -d "Directories to exclude" -r
            complete -c to-codigo -l exclude-ext -d "Extensions to exclude" -r
            complete -c to-codigo -l include-ext -d "Only scan these extensions" -r
            complete -c to-codigo -l no-recursive -d "Do not recurse"
            complete -c to-codigo -l respect-gitignore -d "Respect .gitignore"
            complete -c to-codigo -l workers -d "Number of parallel workers" -r
            complete -c to-codigo -l verbose -d "Show warnings"
            complete -c to-codigo -l no-banner -d "Hide banner"
            complete -c to-codigo -l version -d "Show version"
            complete -c to-codigo -l todos -d "Scan for TODO/FIXME markers"
            complete -c to-codigo -l top -d "Show top N files by LOC" -r
            complete -c to-codigo -l diff -d "Diff against previous JSON report" -r
            complete -c to-codigo -l completion -d "Generate shell completion" -x -a "bash zsh fish"
        """)

    return ""


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Construct and return the argument parser."""
    parser = argparse.ArgumentParser(
        prog="to-codigo",
        description="Analizador de codigo e inventario de proyectos con metricas detalladas.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=True,
        epilog=textwrap.dedent("""
            Examples:
              to-codigo .                               # CSV report
              to-codigo ./src --format html             # HTML Dashboard
              to-codigo . --todos --top 10              # TODO tracking + top files
              to-codigo . --format json --diff old.json # Diff mode
              to-codigo --completion bash               # Shell completion
        """),
    )
    parser.add_argument(
        "ruta_raiz",
        nargs="?",
        default=".",
        help="Carpeta raiz a analizar (default: directorio actual)",
    )
    parser.add_argument(
        "-o", "--output",
        default="reporte",
        help="Nombre base del archivo de salida (sin extension). Default: reporte",
    )
    parser.add_argument(
        "--format",
        choices=["csv", "xlsx", "json", "html", "md"],
        default="csv",
        help="Formato de salida. Default: csv",
    )
    parser.add_argument(
        "--exclude-dirs",
        nargs="*",
        default=list(DEFAULT_EXCLUDE_DIRS),
        help="Directorios a excluir",
    )
    parser.add_argument(
        "--exclude-ext",
        nargs="*",
        default=[],
        help="Extensiones a excluir (con punto, e.g. .log .tmp)",
    )
    parser.add_argument(
        "--include-ext",
        nargs="*",
        default=[],
        help="Solo escanear estas extensiones (con punto, e.g. .py .ts)",
    )
    parser.add_argument(
        "--no-recursive",
        action="store_true",
        help="No escanear recursivamente",
    )
    parser.add_argument(
        "--respect-gitignore",
        action="store_true",
        default=False,
        help="Respetar .gitignore si esta presente",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Numero de procesos paralelos (default: CPU count)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Mostrar warnings de archivos omitidos",
    )
    parser.add_argument(
        "--no-banner",
        action="store_true",
        help="Omitir el banner de inicio",
    )
    parser.add_argument(
        "--todos",
        action="store_true",
        help="Escanear TODO/FIXME/HACK/NOTE markers en comentarios",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=0,
        metavar="N",
        help="Mostrar top N archivos por LOC (0 = desactivado)",
    )
    parser.add_argument(
        "--diff",
        default=None,
        metavar="PATH",
        help="Comparar contra un reporte JSON anterior",
    )
    parser.add_argument(
        "--completion",
        choices=["bash", "zsh", "fish"],
        default=None,
        help="Generar script de autocompletado para shell",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"to-codigo v{VERSION}",
    )
    return parser


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    """Run the CLI.

    Args:
        argv: Optional argument list (defaults to ``sys.argv[1:]``).

    Returns:
        Exit code (0 on success, 1 on error).
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    # --- Shell completion ---
    if args.completion:
        script = _generate_completion(args.completion)
        print(script)
        return 0

    # --- Logging configuration ---
    level = logging.DEBUG if args.verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(levelname)s: %(message)s",
    )

    # --- Banner ---
    if not args.no_banner:
        show_banner(console)

    # --- Validate directory ---
    if not os.path.isdir(args.ruta_raiz):
        show_error(
            f"'{args.ruta_raiz}' no es un directorio valido.",
            hint="Asegurate de pasar la ruta correcta. Ej: to-codigo ./src",
            console=console,
        )
        return 1

    # --- Collect files for progress tracking ---
    excl_dirs = set(DEFAULT_EXCLUDE_DIRS)
    if args.exclude_dirs:
        excl_dirs.update(args.exclude_dirs)

    excl_exts = {e.lower() for e in (args.exclude_ext or [])}
    incl_exts = {e.lower() for e in (args.include_ext or [])}
    gitignore_patterns = _load_gitignore(args.ruta_raiz) if args.respect_gitignore else []

    file_list = _collect_files(
        root=args.ruta_raiz,
        exclude_dirs=excl_dirs,
        exclude_exts=excl_exts,
        include_exts=incl_exts,
        recursive=not args.no_recursive,
        gitignore_patterns=gitignore_patterns,
    )

    if not file_list:
        show_warning(
            "No se encontraron archivos para analizar.",
            console=console,
        )
        return 0

    # --- Determine if todos should be collected ---
    collect_todos = args.todos or args.diff is not None

    # --- Scan with progress bar ---
    start_time = time.time()
    console.print(f"[bold cyan]Escaneando:[/] {args.ruta_raiz}")
    console.print(f"[dim]{len(file_list)} archivos encontrados[/]\n")

    results: list[FileInfo] = []
    all_todos = []

    with create_progress_bar() as progress:
        task = progress.add_task(
            "[cyan]Procesando archivos...",
            total=len(file_list),
        )

        for fpath in file_list:
            info, todos = _process_file(
                (fpath, args.ruta_raiz),
                collect_todos=collect_todos,
            )
            if info is not None:
                results.append(info)
                if collect_todos:
                    all_todos.extend(todos)
            progress.advance(task)

    elapsed = time.time() - start_time

    if not results:
        show_warning(
            "No se pudieron procesar archivos. Revisa los permisos o la codificacion.",
            console=console,
        )
        return 0

    stats = compute_stats(results)

    # --- Results table ---
    show_results_table(stats, len(results), elapsed, console)

    # --- Top files ---
    if args.top > 0:
        show_top_files_table(results, args.top, console)

    # --- TODOs table ---
    if args.todos:
        show_todos_table(all_todos, console)

    # --- Diff mode ---
    if args.diff:
        if not os.path.isfile(args.diff):
            show_error(
                f"Diff file not found: {args.diff}",
                console=console,
            )
        else:
            try:
                with open(args.diff, "r", encoding="utf-8") as f:
                    prev_data = json.load(f)
                diff = diff_reports(results, prev_data)
                show_diff_table(diff, console)
            except (json.JSONDecodeError, KeyError) as e:
                show_error(
                    f"Could not parse diff file: {e}",
                    console=console,
                )

    # --- Generate report ---
    reporter_cls = REPORTERS.get(args.format)
    if reporter_cls is None:
        show_error(
            f"Formato desconocido: {args.format}",
            hint="Formatos validos: csv, xlsx, json, html, md",
            console=console,
        )
        return 1

    output_file = f"{args.output}.{args.format}"
    try:
        reporter_cls().generate(results, stats, output_file)
    except Exception as e:
        show_error(
            f"Error generando reporte: {e}",
            console=console,
        )
        return 1

    show_success(f"Reporte generado: {output_file}", console)
    return 0


if __name__ == "__main__":
    sys.exit(main())
