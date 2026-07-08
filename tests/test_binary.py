"""Unit tests for binary file detection and skipping.

Covers:
- ``is_binary_file()``: null-byte and non-text-ratio heuristic.
- ``count_lines()``: returns ``(0,0,0,0)`` for known binary extensions.
- ``is_binary_path()``: extension-based fast path + content fallback.
- SVG files are NOT treated as binary (they are text/XML).
- ``_process_file`` skips binary files (returns ``(None, [])``).
- ``_process_file`` with ``count_binary=True`` creates a Binary Files entry.
"""

from __future__ import annotations

import struct

from to_codigo.core.counter import count_lines, is_binary_file
from to_codigo.core.scanner import is_binary_path, _process_file


# ---------------------------------------------------------------------------
# is_binary_file() -- content-based heuristic
# ---------------------------------------------------------------------------

def test_is_binary_detects_null_bytes(tmp_path):
    """A file containing NUL bytes is detected as binary."""
    f = tmp_path / "fake.png"
    f.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR" + b"\x00" * 100)
    assert is_binary_file(str(f)) is True


def test_is_binary_detects_high_non_text_ratio(tmp_path):
    """A file with >30% non-text bytes (no NUL) is detected as binary."""
    f = tmp_path / "weird.dat"
    # Bytes 0x80-0xFF are non-text, no NUL.
    f.write_bytes(bytes(range(128, 256)) * 64)
    assert is_binary_file(str(f)) is True


def test_is_binary_false_for_python(tmp_path):
    """A normal Python file is NOT binary."""
    f = tmp_path / "test.py"
    f.write_text("x = 1\nprint(x)\n# comment\n")
    assert is_binary_file(str(f)) is False


def test_is_binary_false_for_plain_text(tmp_path):
    """A plain text file is NOT binary."""
    f = tmp_path / "notes.txt"
    f.write_text("hello world\nthis is text\n")
    assert is_binary_file(str(f)) is False


def test_is_binary_false_for_empty_file(tmp_path):
    """An empty file is NOT binary."""
    f = tmp_path / "empty.txt"
    f.write_text("")
    assert is_binary_file(str(f)) is False


# ---------------------------------------------------------------------------
# count_lines() -- binary guard
# ---------------------------------------------------------------------------

def test_count_lines_returns_zeros_for_png(tmp_path):
    """A .png file must return (0,0,0,0) from count_lines."""
    f = tmp_path / "image.png"
    f.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 500)
    assert count_lines(str(f), "Texto Plano") == (0, 0, 0, 0)


def test_count_lines_returns_zeros_for_jpg(tmp_path):
    """A .jpg file must return (0,0,0,0) from count_lines."""
    f = tmp_path / "photo.jpg"
    f.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 500)
    assert count_lines(str(f), "Texto Plano") == (0, 0, 0, 0)


def test_count_lines_returns_zeros_for_woff(tmp_path):
    """A .woff font file must return (0,0,0,0)."""
    f = tmp_path / "font.woff"
    f.write_bytes(b"wOFF\x00\x01\x00\x00" + b"\x00" * 200)
    assert count_lines(str(f), "Texto Plano") == (0, 0, 0, 0)


def test_count_lines_returns_zeros_for_pdf(tmp_path):
    """A .pdf file must return (0,0,0,0)."""
    f = tmp_path / "doc.pdf"
    f.write_bytes(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n" + b"\x00" * 300)
    assert count_lines(str(f), "Texto Plano") == (0, 0, 0, 0)


def test_count_lines_returns_zeros_for_binary_unknown_ext(tmp_path):
    """A file with unknown extension but binary content returns zeros."""
    f = tmp_path / "data.xyz"
    f.write_bytes(b"\x00\x01\x02\x03" * 100)
    assert count_lines(str(f), "Texto Plano") == (0, 0, 0, 0)


# ---------------------------------------------------------------------------
# count_lines() -- text files still counted correctly
# ---------------------------------------------------------------------------

def test_count_lines_works_for_text_unknown_ext(tmp_path):
    """A text file with unknown extension is still counted."""
    f = tmp_path / "data.xyz"
    f.write_text("line one\nline two\n\n")
    total, code, comment, blank = count_lines(str(f), "Texto Plano")
    assert code == 2
    assert blank == 1
    assert total == 3


# ---------------------------------------------------------------------------
# is_binary_path() -- extension-based fast path
# ---------------------------------------------------------------------------

def test_is_binary_path_by_extension(tmp_path):
    """Known binary extensions are detected by path alone (no file read)."""
    for ext in [".png", ".jpg", ".jpeg", ".gif", ".ico", ".woff", ".woff2",
                ".ttf", ".pdf", ".zip", ".mp4", ".exe", ".dll", ".pyc"]:
        f = tmp_path / f"file{ext}"
        f.write_text("not actually binary but ext is known")
        assert is_binary_path(str(f)) is True, f"Failed for {ext}"


def test_is_binary_path_false_for_code(tmp_path):
    """Source code files are NOT binary."""
    f = tmp_path / "app.py"
    f.write_text("print('hello')\n")
    assert is_binary_path(str(f)) is False


def test_is_binary_path_false_for_svg(tmp_path):
    """SVG files are text/XML, NOT binary."""
    f = tmp_path / "logo.svg"
    f.write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>\n')
    assert is_binary_path(str(f)) is False


def test_is_binary_path_false_for_json(tmp_path):
    """JSON files are text, NOT binary."""
    f = tmp_path / "config.json"
    f.write_text('{"key": "value"}\n')
    assert is_binary_path(str(f)) is False


def test_is_binary_path_content_check_unknown_ext(tmp_path):
    """Unknown extension + binary content = detected as binary."""
    f = tmp_path / "blob.xyz123"
    f.write_bytes(b"\x00\x00\x00\x00" * 50)
    assert is_binary_path(str(f)) is True


def test_is_binary_path_content_check_text_unknown_ext(tmp_path):
    """Unknown extension + text content = NOT binary."""
    f = tmp_path / "notes.xyz123"
    f.write_text("just some text\n")
    assert is_binary_path(str(f)) is False


# ---------------------------------------------------------------------------
# _process_file() -- binary skipping
# ---------------------------------------------------------------------------

def test_process_file_skips_binary(tmp_path):
    """_process_file returns (None, []) for binary files."""
    f = tmp_path / "image.png"
    f.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
    info, todos = _process_file((str(f), str(tmp_path)))
    assert info is None
    assert todos == []


def test_process_file_counts_binary_when_requested(tmp_path):
    """_process_file with count_binary=True creates a Binary Files entry."""
    f = tmp_path / "image.png"
    f.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
    info, todos = _process_file((str(f), str(tmp_path)), count_binary=True)
    assert info is not None
    assert info.language == "Binary Files"
    assert info.total_lines == 0
    assert info.code_lines == 0
    assert info.size_bytes > 0


def test_process_file_processes_svg_as_text(tmp_path):
    """SVG files are processed as text (not skipped as binary)."""
    f = tmp_path / "icon.svg"
    f.write_text('<svg></svg>\n')
    info, todos = _process_file((str(f), str(tmp_path)))
    assert info is not None
    assert info.language == "SVG"
    assert info.total_lines == 1
