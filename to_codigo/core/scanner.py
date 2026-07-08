"""Filesystem scanner with exclusion filtering and multiprocessing.

Exposes :func:`scan_directory` which walks a directory tree, filters files
by extension and exclusion rules, optionally respects ``.gitignore``, and
processes files in parallel using :class:`~concurrent.futures.ProcessPoolExecutor`.

Each file is scanned for line counts AND TODO/FIXME/HACK/NOTE markers.
"""

from __future__ import annotations

import logging
import os
import fnmatch
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Optional

from to_codigo.core.models import FileInfo, LanguageStats, TodoItem
from to_codigo.core.language import detect_language, EXTENSION_MAP, BINARY_EXTENSIONS, FILENAME_MAP
from to_codigo.core.counter import count_lines, scan_markers, is_binary_file

logger = logging.getLogger(__name__)

DEFAULT_EXCLUDE_DIRS: tuple[str, ...] = (
    ".git", "node_modules", "__pycache__", ".vscode",
    ".idea", "venv", ".venv", "env", ".eggs", ".mypy_cache",
    ".pytest_cache", ".tox", "dist", "build",
)


# ---------------------------------------------------------------------------
# Gitignore support (lightweight -- pathspec if available, else fnmatch)
# ---------------------------------------------------------------------------

def _load_gitignore(root: str) -> list[str]:
    """Read ``.gitignore`` patterns from *root* if present.

    Returns an empty list if the file does not exist or cannot be read.
    """
    gitignore_path = os.path.join(root, ".gitignore")
    patterns: list[str] = []
    try:
        with open(gitignore_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.append(line)
    except OSError:
        pass
    return patterns


def _is_ignored(rel_path: str, patterns: list[str]) -> bool:
    """Check whether *rel_path* matches any gitignore-style pattern."""
    try:
        import pathspec  # type: ignore
        spec = pathspec.PathSpec.from_lines("gitwildmatch", patterns)
        return spec.match_file(rel_path)
    except ImportError:
        # Fallback: simple fnmatch against each pattern.
        basename = os.path.basename(rel_path)
        for pat in patterns:
            if fnmatch.fnmatch(rel_path, pat) or fnmatch.fnmatch(basename, pat):
                return True
        return False


# ---------------------------------------------------------------------------
# File collection
# ---------------------------------------------------------------------------

def _collect_files(
    root: str,
    exclude_dirs: set[str],
    exclude_exts: set[str],
    include_exts: set[str],
    recursive: bool,
    gitignore_patterns: list[str],
) -> list[str]:
    """Walk *root* and return a list of absolute file paths to process."""
    files: list[str] = []

    if recursive:
        for dirpath, dirnames, filenames in os.walk(root):
            # Mutate dirnames in-place to prune excluded directories.
            dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
            for fname in filenames:
                abs_path = os.path.join(dirpath, fname)
                rel_path = os.path.relpath(abs_path, root)
                if gitignore_patterns and _is_ignored(rel_path, gitignore_patterns):
                    continue
                files.append(abs_path)
    else:
        # Non-recursive: use os.scandir for efficiency.
        try:
            with os.scandir(root) as entries:
                for entry in entries:
                    if entry.is_file():
                        rel_path = os.path.relpath(entry.path, root)
                        if gitignore_patterns and _is_ignored(rel_path, gitignore_patterns):
                            continue
                        files.append(entry.path)
        except OSError as e:
            logger.warning("Cannot scan %s: %s", root, e)

    # Extension filtering.
    result: list[str] = []
    for fpath in files:
        ext = os.path.splitext(fpath)[1].lower()
        if exclude_exts and ext in exclude_exts:
            continue
        if include_exts and ext not in include_exts:
            continue
        result.append(fpath)

    return result


# ---------------------------------------------------------------------------
# Worker (module-level for picklability with ProcessPoolExecutor)
# ---------------------------------------------------------------------------

def is_binary_path(filepath: str) -> bool:
    """Quickly determine if *filepath* points to a binary file.

    Checks the extension against ``BINARY_EXTENSIONS`` first (fast path),
    then falls back to a null-byte content check for unknown extensions.

    Args:
        filepath: Absolute or relative path to the file.

    Returns:
        ``True`` if the file is binary, ``False`` otherwise.
    """
    ext = os.path.splitext(filepath)[1].lower()
    if ext in BINARY_EXTENSIONS:
        return True
    if ext not in EXTENSION_MAP:
        filename_lower = os.path.basename(filepath).lower()
        if filename_lower not in FILENAME_MAP:
            return is_binary_file(filepath)
    return False


def _process_file(
    args: tuple[str, str],
    collect_todos: bool = True,
    count_binary: bool = False,
) -> tuple[Optional[FileInfo], list[TodoItem]]:
    """Process a single file and return a ``(FileInfo, list[TodoItem])`` tuple.

    Returns ``(None, [])`` on error or when a binary file is skipped.

    This function must remain at module level so that ``ProcessPoolExecutor``
    can pickle it.

    Args:
        args: A ``(abs_path, root)`` tuple.
        collect_todos: If ``True``, scan for TODO/FIXME/HACK/NOTE markers.
        count_binary: If ``True``, create a ``FileInfo`` with language
            ``"Binary Files"`` (0 lines, correct size) instead of skipping.
    """
    abs_path, root = args
    try:
        filename = os.path.basename(abs_path)
        dir_path = os.path.dirname(abs_path)
        relative_path = os.path.relpath(dir_path, root) if dir_path != root else "."
        size, modified_at = _get_file_info(abs_path)

        # --- Binary detection ---
        if is_binary_path(abs_path):
            if count_binary:
                return FileInfo(
                    absolute_path=abs_path,
                    relative_path=relative_path,
                    filename=filename,
                    language="Binary Files",
                    size_bytes=size,
                    modified_at=modified_at,
                    total_lines=0,
                    code_lines=0,
                    comment_lines=0,
                    blank_lines=0,
                ), []
            logger.debug("Skipping binary file: %s", abs_path)
            return None, []

        language = detect_language(abs_path)
        total, code, comment, blank = count_lines(abs_path, language)

        if collect_todos:
            todo_items = scan_markers(abs_path, language)
            todos = sum(1 for t in todo_items if t.marker == "TODO")
            fixmes = sum(1 for t in todo_items if t.marker in ("FIXME", "BUG"))
            hacks = sum(1 for t in todo_items if t.marker in ("HACK", "XXX"))
            notes = sum(1 for t in todo_items if t.marker == "NOTE")
        else:
            todo_items = []
            todos = fixmes = hacks = notes = 0

        return FileInfo(
            absolute_path=abs_path,
            relative_path=relative_path,
            filename=filename,
            language=language,
            size_bytes=size,
            modified_at=modified_at,
            total_lines=total,
            code_lines=code,
            comment_lines=comment,
            blank_lines=blank,
            todos=todos,
            fixmes=fixmes,
            hacks=hacks,
            notes=notes,
        ), todo_items
    except (OSError, UnicodeDecodeError) as e:
        logger.warning("Skipping %s: %s", abs_path, e)
        return None, []


def _get_file_info(path: str) -> tuple[int, str]:
    """Return ``(size_bytes, modified_at_string)`` for *path*."""
    try:
        stat = os.stat(path)
        size = stat.st_size
        mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        return size, mtime
    except OSError as e:
        logger.warning("Could not stat %s: %s", path, e)
        return 0, "N/A"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def scan_directory(
    root: str,
    exclude_dirs: list[str] | None = None,
    exclude_exts: list[str] | None = None,
    include_exts: list[str] | None = None,
    recursive: bool = True,
    respect_gitignore: bool = False,
    max_workers: int | None = None,
    collect_todos: bool = False,
    count_binary: bool = False,
) -> tuple[list[FileInfo], list[TodoItem]]:
    """Scan *root* and return a tuple of ``(FileInfo list, TodoItem list)``.

    Args:
        root: Directory to scan.
        exclude_dirs: Directory names to skip (merged with defaults).
        exclude_exts: File extensions to exclude (e.g. ``[".log", ".tmp"]``).
        include_exts: If non-empty, **only** scan these extensions.
        recursive: Whether to descend into subdirectories.
        respect_gitignore: If ``True``, honour a ``.gitignore`` in *root*.
        max_workers: Number of parallel worker processes (default: CPU count).
        collect_todos: If ``True``, scan each file for TODO/FIXME/HACK/NOTE
            markers and populate ``FileInfo`` todo fields.
        count_binary: If ``True``, binary files get a ``FileInfo`` entry with
            language ``"Binary Files"`` (0 lines, correct size) instead of
            being skipped silently.

    Returns:
        A tuple ``(results, all_todos)`` where *results* is a list of
        ``FileInfo`` objects and *all_todos* is a flat list of all
        ``TodoItem`` objects found (empty when *collect_todos* is ``False``).
    """
    if not os.path.isdir(root):
        raise NotADirectoryError(f"'{root}' is not a valid directory")

    # Merge exclude dirs with defaults.
    excl_dirs = set(DEFAULT_EXCLUDE_DIRS)
    if exclude_dirs:
        excl_dirs.update(exclude_dirs)

    excl_exts = {e.lower() for e in exclude_exts} if exclude_exts else set()
    incl_exts = {e.lower() for e in include_exts} if include_exts else set()

    gitignore_patterns = _load_gitignore(root) if respect_gitignore else []

    file_list = _collect_files(
        root=root,
        exclude_dirs=excl_dirs,
        exclude_exts=excl_exts,
        include_exts=incl_exts,
        recursive=recursive,
        gitignore_patterns=gitignore_patterns,
    )

    if not file_list:
        return [], []

    results: list[FileInfo] = []
    all_todos: list[TodoItem] = []
    tasks = [(fpath, root) for fpath in file_list]

    # Use multiprocessing for CPU-bound line counting.
    try:
        with ProcessPoolExecutor(max_workers=max_workers) as pool:
            futures = {
                pool.submit(_process_file, task, collect_todos, count_binary): task
                for task in tasks
            }
            for future in as_completed(futures):
                info, todos = future.result()
                if info is not None:
                    results.append(info)
                    if collect_todos:
                        all_todos.extend(todos)
    except Exception as e:
        logger.error("Parallel processing failed, falling back to serial: %s", e)
        for task in tasks:
            info, todos = _process_file(task, collect_todos=collect_todos, count_binary=count_binary)
            if info is not None:
                results.append(info)
                if collect_todos:
                    all_todos.extend(todos)

    return results, all_todos


def compute_stats(files: list[FileInfo]) -> dict[str, LanguageStats]:
    """Aggregate per-language statistics from a list of :class:`FileInfo`.

    Args:
        files: List of ``FileInfo`` objects.

    Returns:
        A dict mapping language name to :class:`LanguageStats`.
    """
    stats: dict[str, LanguageStats] = {}
    for info in files:
        if info.language not in stats:
            stats[info.language] = LanguageStats()
        stats[info.language].add(info)
    return stats
