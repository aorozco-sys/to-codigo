"""Unit tests for TODO/FIXME/HACK/XXX/BUG/NOTE marker detection."""

from __future__ import annotations

from to_codigo.core.counter import scan_markers


# ---------------------------------------------------------------------------
# Python -- hash comments
# ---------------------------------------------------------------------------

def test_python_todo(tmp_path):
    """TODO detection in Python (# TODO: ...)."""
    f = tmp_path / "test.py"
    f.write_text(
        "# TODO: fix this function\n"
        "x = 1\n"
        "# FIXME: broken logic\n"
        "# NOTE: this is important\n"
    )
    items = scan_markers(str(f), "Python")
    markers = [i.marker for i in items]
    assert "TODO" in markers
    assert "FIXME" in markers
    assert "NOTE" in markers
    assert len(items) == 3


def test_python_todo_text(tmp_path):
    """The descriptive text is captured correctly."""
    f = tmp_path / "app.py"
    f.write_text("# TODO: refactor this module\n")
    items = scan_markers(str(f), "Python")
    assert len(items) == 1
    assert items[0].marker == "TODO"
    assert "refactor" in items[0].text


def test_python_todo_line_number(tmp_path):
    """Line numbers are 1-based and correct."""
    f = tmp_path / "lines.py"
    f.write_text(
        "x = 1\n"
        "y = 2\n"
        "# TODO: line 3\n"
    )
    items = scan_markers(str(f), "Python")
    assert len(items) == 1
    assert items[0].line_number == 3


# ---------------------------------------------------------------------------
# JavaScript -- // comments
# ---------------------------------------------------------------------------

def test_javascript_fixme(tmp_path):
    """FIXME detection in JavaScript (// FIXME: ...)."""
    f = tmp_path / "test.js"
    f.write_text(
        "// FIXME: broken callback\n"
        "const x = 1;\n"
        "// TODO: add error handling\n"
    )
    items = scan_markers(str(f), "JavaScript")
    markers = [i.marker for i in items]
    assert "FIXME" in markers
    assert "TODO" in markers
    assert len(items) == 2


def test_javascript_block_comment_hack(tmp_path):
    """HACK detection inside C-style block comments."""
    f = tmp_path / "hack.js"
    f.write_text(
        "/* HACK: workaround for IE bug */\n"
        "const x = 1;\n"
    )
    items = scan_markers(str(f), "JavaScript")
    assert len(items) == 1
    assert items[0].marker == "HACK"


# ---------------------------------------------------------------------------
# PHP -- # comments (validates the PHP fix for markers too)
# ---------------------------------------------------------------------------

def test_php_hash_todo(tmp_path):
    """TODO detection using PHP hash (#) comments -- validates PHP fix."""
    f = tmp_path / "test.php"
    f.write_text(
        "# TODO: fix this PHP code\n"
        "// FIXME: also broken\n"
        "$x = 1;\n"
    )
    items = scan_markers(str(f), "PHP")
    markers = [i.marker for i in items]
    assert "TODO" in markers
    assert "FIXME" in markers
    assert len(items) == 2


def test_php_hash_hack(tmp_path):
    """HACK detection using PHP hash (#) comments."""
    f = tmp_path / "hack.php"
    f.write_text(
        "# HACK: workaround\n"
        "$x = 1;\n"
    )
    items = scan_markers(str(f), "PHP")
    assert len(items) == 1
    assert items[0].marker == "HACK"


# ---------------------------------------------------------------------------
# No false positives
# ---------------------------------------------------------------------------

def test_no_markers_in_clean_file(tmp_path):
    """Files with no markers return empty list."""
    f = tmp_path / "clean.py"
    f.write_text(
        "# This is a regular comment\n"
        "x = 1\n"
    )
    items = scan_markers(str(f), "Python")
    assert items == []


def test_no_false_positive_in_string(tmp_path):
    """'TODO' inside a string literal should NOT be detected
    when it's not preceded by a comment prefix."""
    f = tmp_path / "strings.py"
    f.write_text(
        'msg = "TODO: this is a string not a comment"\n'
        'print(msg)\n'
    )
    items = scan_markers(str(f), "Python")
    assert items == []


def test_no_false_positive_in_code(tmp_path):
    """A variable named todoFunction should not trigger."""
    f = tmp_path / "nocode.py"
    f.write_text(
        "def todo_list():\n"
        "    return []\n"
    )
    items = scan_markers(str(f), "Python")
    assert items == []


# ---------------------------------------------------------------------------
# Multiple markers in one file
# ---------------------------------------------------------------------------

def test_multiple_markers(tmp_path):
    """Multiple different markers in one file are all detected."""
    f = tmp_path / "complex.py"
    f.write_text(
        "# TODO: first task\n"
        "# FIXME: second bug\n"
        "# HACK: third workaround\n"
        "# NOTE: fourth note\n"
        "# BUG: fifth issue\n"
        "# XXX: sixth warning\n"
    )
    items = scan_markers(str(f), "Python")
    markers = sorted(i.marker for i in items)
    assert markers == ["BUG", "FIXME", "HACK", "NOTE", "TODO", "XXX"]


def test_multiple_markers_different_languages(tmp_path):
    """Markers are detected across different comment styles."""
    f_py = tmp_path / "a.py"
    f_py.write_text("# TODO: python task\n")
    assert len(scan_markers(str(f_py), "Python")) == 1

    f_js = tmp_path / "b.js"
    f_js.write_text("// FIXME: js bug\n")
    assert len(scan_markers(str(f_js), "JavaScript")) == 1

    f_go = tmp_path / "c.go"
    f_go.write_text("// HACK: go hack\n")
    assert len(scan_markers(str(f_go), "Go")) == 1
