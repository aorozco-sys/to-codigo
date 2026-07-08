"""Diff engine for comparing a current scan against a previous JSON report.

Given a list of :class:`~to_codigo.core.models.FileInfo` from the current scan
and a parsed JSON dict from a previous report, :func:`diff_reports` computes
the differences: files added/removed/modified, LOC changes per language, and
TODOs added/resolved.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from to_codigo.core.models import FileInfo


@dataclass
class DiffResult:
    """Result of comparing two analysis snapshots.

    Attributes:
        added_files: Filenames present in current but not in previous.
        removed_files: Filenames present in previous but not in current.
        modified_files: Filenames present in both but with changed LOC.
        loc_changes_by_language: Net LOC change per language
            (positive = growth, negative = shrink).
        new_todos: Number of TODO/FIXME markers added since previous scan.
        resolved_todos: Number of TODO/FIXME markers removed since previous scan.
    """

    added_files: list[str] = field(default_factory=list)
    removed_files: list[str] = field(default_factory=list)
    modified_files: list[str] = field(default_factory=list)
    loc_changes_by_language: dict[str, int] = field(default_factory=dict)
    new_todos: int = 0
    resolved_todos: int = 0


def diff_reports(
    current_files: list[FileInfo],
    previous_json: dict,
) -> DiffResult:
    """Compare a current scan against a previous JSON report.

    Args:
        current_files: List of ``FileInfo`` objects from the current scan.
        previous_json: Parsed JSON dict from a previous report (as produced by
            :class:`~to_codigo.core.reporter.JSONReporter`).

    Returns:
        A :class:`DiffResult` with the computed differences.
    """
    # --- Build previous file lookup by filename ---
    prev_files: dict[str, dict] = {}
    for f in previous_json.get("files", []):
        prev_files[f.get("filename", "")] = f

    # --- Build current file lookup by filename ---
    curr_files: dict[str, FileInfo] = {f.filename: f for f in current_files}

    prev_names = set(prev_files.keys())
    curr_names = set(curr_files.keys())

    added = sorted(curr_names - prev_names)
    removed = sorted(prev_names - curr_names)

    # --- Modified files (LOC changed) ---
    modified: list[str] = []
    for name in sorted(curr_names & prev_names):
        prev_loc = prev_files[name].get("code_lines", 0)
        curr_loc = curr_files[name].code_lines
        if prev_loc != curr_loc:
            modified.append(name)

    # --- LOC changes per language ---
    loc_changes: dict[str, int] = {}

    # Previous LOC by language (from summary or reconstruct from files).
    prev_summary = previous_json.get("summary", {})
    for lang, data in prev_summary.items():
        loc_changes[lang] = loc_changes.get(lang, 0) - data.get("total_code_lines", 0)

    # Current LOC by language.
    for info in current_files:
        loc_changes[info.language] = loc_changes.get(info.language, 0) + info.code_lines

    # Remove zero entries.
    loc_changes = {k: v for k, v in loc_changes.items() if v != 0}

    # --- TODO/FIXME tracking ---
    def _curr_todo_count(info: FileInfo) -> int:
        return info.todos + info.fixmes

    def _prev_todo_count(fdata: dict) -> int:
        return fdata.get("todos", 0) + fdata.get("fixmes", 0)

    prev_todo_files: dict[str, int] = {}
    for name, fdata in prev_files.items():
        count = _prev_todo_count(fdata)
        if count > 0:
            prev_todo_files[name] = count

    curr_todo_files: dict[str, int] = {}
    for name, info in curr_files.items():
        count = _curr_todo_count(info)
        if count > 0:
            curr_todo_files[name] = count

    new_todos = 0
    for name, count in curr_todo_files.items():
        prev_count = prev_todo_files.get(name, 0)
        if count > prev_count:
            new_todos += count - prev_count

    resolved_todos = 0
    for name, count in prev_todo_files.items():
        curr_count = curr_todo_files.get(name, 0)
        if count > curr_count:
            resolved_todos += count - curr_count

    return DiffResult(
        added_files=added,
        removed_files=removed,
        modified_files=modified,
        loc_changes_by_language=loc_changes,
        new_todos=new_todos,
        resolved_todos=resolved_todos,
    )
