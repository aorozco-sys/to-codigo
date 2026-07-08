"""Line-counting engine and marker scanner.

Replaces the original hardcoded ``if/elif`` chain with a data-driven
state machine powered by :class:`~to_codigo.core.language.LanguageConfig`.

The counter handles:
- Single-line (full-line) comments.
- Block / multi-line comments spanning multiple lines.
- Inline comments (code followed by a comment -- counted as **code**).
- Block comments that open mid-line and continue to subsequent lines.

The marker scanner (:func:`scan_markers`) finds TODO/FIXME/HACK/XXX/BUG/NOTE
markers in comments using language-aware regex patterns.
"""

from __future__ import annotations

import logging
import os
import re

from to_codigo.core.language import get_language_config, BINARY_EXTENSIONS
from to_codigo.core.models import TodoItem

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Marker detection
# ---------------------------------------------------------------------------

MARKERS: tuple[str, ...] = ("TODO", "FIXME", "HACK", "XXX", "BUG", "NOTE")


def _build_marker_regex(language: str) -> re.Pattern[str]:
    """Build a regex pattern for detecting markers in *language* comments.

    The pattern matches a comment prefix (specific to the language) followed
    by one of the known marker keywords and optional descriptive text.
    """
    config = get_language_config(language)
    prefixes: list[str] = []
    if config:
        prefixes.extend(config.line_comments)
        for start, _ in config.block_comment_pairs:
            prefixes.append(start)
    if not prefixes:
        prefixes = ["#"]

    escaped = "|".join(re.escape(p) for p in prefixes)

    return re.compile(
        rf"(?:{escaped})\s*"
        r"(TODO|FIXME|HACK|XXX|BUG|NOTE)\b"
        r"\s*:?\s*"
        r"(.*)",
        re.IGNORECASE,
    )


def scan_markers(filepath: str, language: str) -> list[TodoItem]:
    """Scan a file for TODO/FIXME/HACK/XXX/BUG/NOTE markers.

    Uses a language-aware regex that respects each language's comment
    syntax (``#`` for Python, ``//`` for JavaScript, ``/*`` for C-style
    block comments, ``--`` for SQL/Lua/Haskell, etc.).

    Args:
        filepath: Path to the source file.
        language: Language name (must exist in ``LANGUAGE_CONFIGS``).

    Returns:
        A list of :class:`TodoItem` objects, one per marker found.
    """
    pattern = _build_marker_regex(language)
    items: list[TodoItem] = []
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line_num, raw_line in enumerate(f, 1):
                m = pattern.search(raw_line)
                if m:
                    marker = m.group(1).upper()
                    text = m.group(2).strip()
                    items.append(TodoItem(
                        filepath=filepath,
                        line_number=line_num,
                        marker=marker,
                        text=text,
                    ))
    except (OSError, UnicodeDecodeError) as e:
        logger.warning("Could not scan markers in %s: %s", filepath, e)

    return items


# ---------------------------------------------------------------------------
# Binary detection
# ---------------------------------------------------------------------------

def is_binary_file(filepath: str, sample_size: int = 8192) -> bool:
    """Detect if a file is binary by checking for null bytes in the first chunk.

    Uses a two-stage heuristic inspired by git's binary detection:
    1. If a NUL byte (``\\x00``) is found, the file is binary.
    2. If more than 30 % of the sampled bytes are non-text, the file is binary.

    Args:
        filepath: Path to the file to check.
        sample_size: Number of bytes to read for the heuristic (default 8 KiB).

    Returns:
        ``True`` if the file appears to be binary, ``False`` otherwise.
        Returns ``True`` on read errors (safer to skip than to crash).
    """
    try:
        with open(filepath, "rb") as f:
            chunk = f.read(sample_size)
    except (OSError, IOError):
        return True

    if not chunk:
        return False

    if b"\x00" in chunk:
        return True

    text_chars = bytes(range(32, 127)) + b"\n\r\t\f\b"
    non_text = sum(1 for b in chunk if b not in text_chars)
    if non_text / len(chunk) > 0.30:
        return True

    return False


# ---------------------------------------------------------------------------
# Line counting
# ---------------------------------------------------------------------------

def count_lines(filepath: str, language: str) -> tuple[int, int, int, int]:
    """Count lines in a file, classifying each as code, comment, or blank.

    Binary files (known extensions or null-byte detected) return ``(0, 0, 0, 0)``.

    Args:
        filepath: Path to the source file.
        language: Language name (must exist in ``LANGUAGE_CONFIGS``).

    Returns:
        A 4-tuple ``(total_lines, code_lines, comment_lines, blank_lines)``.
    """
    # --- Binary guard: known binary extensions ---
    ext = os.path.splitext(filepath)[1].lower()
    if ext in BINARY_EXTENSIONS:
        return 0, 0, 0, 0

    # --- Binary guard: content-based heuristic for unknown extensions ---
    if language == "Texto Plano":
        if is_binary_file(filepath):
            return 0, 0, 0, 0

    config = get_language_config(language)

    total = code = comment = blank = 0
    in_block_comment = False
    block_end: str | None = None

    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for raw_line in f:
                total += 1
                stripped = raw_line.strip()

                # --- Blank line -------------------------------------------------
                if not stripped:
                    blank += 1
                    continue

                # --- Inside a multi-line block comment -------------------------
                if in_block_comment:
                    comment += 1
                    if block_end and block_end in stripped:
                        in_block_comment = False
                        block_end = None
                    continue

                # --- Not in a block comment: classify the line -----------------

                # 1) Block-comment open on this line? (checked FIRST so that
                #    multi-char openers like Lua's ``--[[`` win over the ``--``
                #    line-comment prefix.)
                if config and config.block_comment_pairs:
                    handled = False
                    for bstart, bend in config.block_comment_pairs:
                        idx = stripped.find(bstart)
                        if idx == -1:
                            continue
                        before = stripped[:idx].strip()
                        close_idx = stripped.find(bend, idx + len(bstart))
                        if close_idx != -1:
                            # Block opens AND closes on the same line.
                            after = stripped[close_idx + len(bend):].strip()
                            if before or after:
                                code += 1
                            else:
                                comment += 1
                        else:
                            # Block continues to subsequent lines.
                            if before:
                                code += 1
                            else:
                                comment += 1
                            in_block_comment = True
                            block_end = bend
                        handled = True
                        break
                    if handled:
                        continue

                # 2) Full-line single-line comment?
                if config and config.line_comments:
                    if any(stripped.startswith(lc) for lc in config.line_comments):
                        comment += 1
                        continue

                # 3) Regular code line
                code += 1

    except (OSError, UnicodeDecodeError) as e:
        logger.warning("Could not read %s: %s", filepath, e)

    return total, code, comment, blank
