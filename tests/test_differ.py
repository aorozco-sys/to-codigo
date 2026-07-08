"""Unit tests for the diff engine."""

from __future__ import annotations

import json

from to_codigo.core.differ import diff_reports, DiffResult
from to_codigo.core.models import FileInfo


def _make_file(
    filename: str = "test.py",
    language: str = "Python",
    code_lines: int = 10,
    comment_lines: int = 2,
    blank_lines: int = 1,
    todos: int = 0,
    fixmes: int = 0,
) -> FileInfo:
    """Convenience factory for building FileInfo in tests."""
    return FileInfo(
        absolute_path=f"/project/{filename}",
        relative_path=".",
        filename=filename,
        language=language,
        size_bytes=100,
        modified_at="2025-01-01 00:00:00",
        total_lines=code_lines + comment_lines + blank_lines,
        code_lines=code_lines,
        comment_lines=comment_lines,
        blank_lines=blank_lines,
        todos=todos,
        fixmes=fixmes,
    )


def _make_prev_json(files: list[dict], summary: dict | None = None) -> dict:
    """Build a previous report JSON dict."""
    return {
        "files": files,
        "summary": summary or {},
    }


# ---------------------------------------------------------------------------
# Added files
# ---------------------------------------------------------------------------

def test_diff_added_files():
    """Files in current but not in previous are detected as added."""
    prev = _make_prev_json(
        [{"filename": "old.py", "code_lines": 10, "language": "Python", "todos": 0, "fixmes": 0}],
        summary={"Python": {"total_code_lines": 10}},
    )
    curr = [_make_file("old.py", code_lines=10), _make_file("new.py", code_lines=20)]
    diff = diff_reports(curr, prev)
    assert "new.py" in diff.added_files
    assert "old.py" not in diff.added_files


# ---------------------------------------------------------------------------
# Removed files
# ---------------------------------------------------------------------------

def test_diff_removed_files():
    """Files in previous but not in current are detected as removed."""
    prev = _make_prev_json(
        [
            {"filename": "keep.py", "code_lines": 10, "language": "Python", "todos": 0, "fixmes": 0},
            {"filename": "gone.py", "code_lines": 30, "language": "Python", "todos": 0, "fixmes": 0},
        ],
        summary={"Python": {"total_code_lines": 40}},
    )
    curr = [_make_file("keep.py", code_lines=10)]
    diff = diff_reports(curr, prev)
    assert "gone.py" in diff.removed_files
    assert "keep.py" not in diff.removed_files


# ---------------------------------------------------------------------------
# LOC changes
# ---------------------------------------------------------------------------

def test_diff_loc_growth():
    """LOC growth is reflected as positive loc_changes_by_language."""
    prev = _make_prev_json(
        [{"filename": "growing.py", "code_lines": 10, "language": "Python", "todos": 0, "fixmes": 0}],
        summary={"Python": {"total_code_lines": 10}},
    )
    curr = [_make_file("growing.py", code_lines=50)]
    diff = diff_reports(curr, prev)
    assert diff.loc_changes_by_language.get("Python", 0) == 40


def test_diff_loc_shrink():
    """LOC shrink is reflected as negative loc_changes_by_language."""
    prev = _make_prev_json(
        [{"filename": "shrinking.py", "code_lines": 100, "language": "Python", "todos": 0, "fixmes": 0}],
        summary={"Python": {"total_code_lines": 100}},
    )
    curr = [_make_file("shrinking.py", code_lines=30)]
    diff = diff_reports(curr, prev)
    assert diff.loc_changes_by_language.get("Python", 0) == -70


def test_diff_modified_files():
    """Files with changed LOC are listed in modified_files."""
    prev = _make_prev_json(
        [{"filename": "changed.py", "code_lines": 10, "language": "Python", "todos": 0, "fixmes": 0}],
        summary={"Python": {"total_code_lines": 10}},
    )
    curr = [_make_file("changed.py", code_lines=25)]
    diff = diff_reports(curr, prev)
    assert "changed.py" in diff.modified_files


def test_diff_no_changes():
    """Identical scans produce zero diffs."""
    prev = _make_prev_json(
        [{"filename": "stable.py", "code_lines": 50, "language": "Python", "todos": 0, "fixmes": 0}],
        summary={"Python": {"total_code_lines": 50}},
    )
    curr = [_make_file("stable.py", code_lines=50)]
    diff = diff_reports(curr, prev)
    assert diff.added_files == []
    assert diff.removed_files == []
    assert diff.modified_files == []
    assert diff.loc_changes_by_language == {}
