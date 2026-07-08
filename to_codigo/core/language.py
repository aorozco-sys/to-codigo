"""Language detection and comment-syntax configuration.

Provides:
- ``EXTENSION_MAP``: file-extension to language-name lookup.
- ``LanguageConfig``: frozen dataclass describing comment syntax per language.
- ``LANGUAGE_CONFIGS``: registry mapping language names to their configs.
- ``detect_language()``: detects language from extension, falling back to shebang.
"""

from __future__ import annotations

import os
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Extension to language mapping
# ---------------------------------------------------------------------------

EXTENSION_MAP: dict[str, str] = {
    ".py":   "Python",
    ".js":   "JavaScript",
    ".ts":   "TypeScript",
    ".jsx":  "React (JS)",
    ".tsx":  "React (TS)",
    ".java": "Java",
    ".cs":   "C#",
    ".c":    "C",
    ".cpp":  "C++",
    ".cc":   "C++",
    ".cxx":  "C++",
    ".hpp":  "C++",
    ".h":    "C/C++",
    ".go":   "Go",
    ".rs":   "Rust",
    ".rb":   "Ruby",
    ".php":  "PHP",
    ".pl":   "Perl",
    ".sh":   "Shell",
    ".bash": "Bash",
    ".sql":  "SQL",
    ".html": "HTML",
    ".htm":  "HTML",
    ".css":  "CSS",
    ".scss": "SCSS",
    ".sass": "Sass",
    ".less": "Less",
    ".xml":  "XML",
    ".json": "JSON",
    ".yaml": "YAML",
    ".yml":  "YAML",
    ".md":   "Markdown",
    ".txt":  "Texto Plano",
    ".r":    "R",
    ".m":    "MATLAB",
    ".swift": "Swift",
    ".kt":   "Kotlin",
    ".scala": "Scala",
    ".clj":  "Clojure",
    ".hs":   "Haskell",
    ".lua":  "Lua",
    ".dart": "Dart",
    ".ex":   "Elixir",
    ".exs":  "Elixir",
}

# ---------------------------------------------------------------------------
# Comment-syntax configuration (data-driven)
# ---------------------------------------------------------------------------

_NO_COMMENTS: tuple = ()

_C_STYLE: tuple[tuple[str, str], ...] = (("/*", "*/"),)


@dataclass(frozen=True)
class LanguageConfig:
    """Describes the comment syntax for a single language.

    Attributes:
        name: Human-readable language name (matches ``EXTENSION_MAP`` values).
        line_comments: Prefixes that start a single-line comment
            (e.g. ``("#",)`` for Python, ``("//", "#")`` for PHP).
        block_comment_pairs: Tuples of ``(open, close)`` delimiters for
            multi-line / block comments (e.g. ``(("/*", "*/"),)``).
    """

    name: str
    line_comments: tuple[str, ...] = ()
    block_comment_pairs: tuple[tuple[str, str], ...] = ()


def _cfg(
    name: str,
    line_comments: tuple[str, ...] = (),
    block_comment_pairs: tuple[tuple[str, str], ...] = (),
) -> LanguageConfig:
    """Convenience factory for building ``LanguageConfig`` entries."""
    return LanguageConfig(
        name=name,
        line_comments=line_comments,
        block_comment_pairs=block_comment_pairs,
    )


LANGUAGE_CONFIGS: dict[str, LanguageConfig] = {
    # --- Hash-comment family ---
    "Python":  _cfg("Python", line_comments=("#",)),
    "Ruby":    _cfg("Ruby", line_comments=("#",)),
    "Perl":    _cfg("Perl", line_comments=("#",)),
    "Shell":   _cfg("Shell", line_comments=("#",)),
    "Bash":    _cfg("Bash", line_comments=("#",)),
    "R":       _cfg("R", line_comments=("#",)),
    "Elixir":  _cfg("Elixir", line_comments=("#",)),
    "YAML":    _cfg("YAML", line_comments=("#",)),
    "Clojure": _cfg("Clojure", line_comments=(";",)),

    # --- C-style family (// + /* */) ---
    "JavaScript": _cfg("JavaScript", line_comments=("//",), block_comment_pairs=_C_STYLE),
    "TypeScript": _cfg("TypeScript", line_comments=("//",), block_comment_pairs=_C_STYLE),
    "React (JS)": _cfg("React (JS)", line_comments=("//",), block_comment_pairs=_C_STYLE),
    "React (TS)": _cfg("React (TS)", line_comments=("//",), block_comment_pairs=_C_STYLE),
    "Java":       _cfg("Java", line_comments=("//",), block_comment_pairs=_C_STYLE),
    "C#":         _cfg("C#", line_comments=("//",), block_comment_pairs=_C_STYLE),
    "C":          _cfg("C", line_comments=("//",), block_comment_pairs=_C_STYLE),
    "C++":        _cfg("C++", line_comments=("//",), block_comment_pairs=_C_STYLE),
    "C/C++":      _cfg("C/C++", line_comments=("//",), block_comment_pairs=_C_STYLE),
    "Go":         _cfg("Go", line_comments=("//",), block_comment_pairs=_C_STYLE),
    "Rust":       _cfg("Rust", line_comments=("//",), block_comment_pairs=_C_STYLE),
    "Swift":      _cfg("Swift", line_comments=("//",), block_comment_pairs=_C_STYLE),
    "Kotlin":     _cfg("Kotlin", line_comments=("//",), block_comment_pairs=_C_STYLE),
    "Scala":      _cfg("Scala", line_comments=("//",), block_comment_pairs=_C_STYLE),
    "Dart":       _cfg("Dart", line_comments=("//",), block_comment_pairs=_C_STYLE),
    "SCSS":       _cfg("SCSS", line_comments=("//",), block_comment_pairs=_C_STYLE),
    "Sass":       _cfg("Sass", line_comments=("//",), block_comment_pairs=_C_STYLE),
    "Less":       _cfg("Less", line_comments=("//",), block_comment_pairs=_C_STYLE),

    # --- PHP: // + # + /* */ ---
    "PHP": _cfg("PHP", line_comments=("//", "#"), block_comment_pairs=_C_STYLE),

    # --- SQL ---
    "SQL": _cfg("SQL", line_comments=("--",), block_comment_pairs=_C_STYLE),

    # --- MATLAB: % + %{ %} ---
    "MATLAB": _cfg("MATLAB", line_comments=("%",), block_comment_pairs=(("%{", "%}"),)),

    # --- Haskell: -- + {- -} ---
    "Haskell": _cfg("Haskell", line_comments=("--",), block_comment_pairs=(("{-", "-}"),)),

    # --- Lua: -- + --[[ ]] ---
    "Lua": _cfg("Lua", line_comments=("--",), block_comment_pairs=(("--[[", "]]"),)),

    # --- Markup languages (block comments only) ---
    "HTML": _cfg("HTML", block_comment_pairs=(("<!--", "-->"),)),
    "XML":  _cfg("XML", block_comment_pairs=(("<!--", "-->"),)),
    "CSS":  _cfg("CSS", block_comment_pairs=_C_STYLE),

    # --- No meaningful comments (data / plain text) ---
    "JSON":        _cfg("JSON"),
    "Markdown":    _cfg("Markdown"),
    "Texto Plano": _cfg("Texto Plano"),
}


def get_language_config(language: str) -> LanguageConfig | None:
    """Return the comment configuration for *language*, or ``None`` if unknown."""
    return LANGUAGE_CONFIGS.get(language)


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------

def detect_language(filepath: str) -> str:
    """Detect the programming language of a file.

    Strategy:
    1. Check the file extension against ``EXTENSION_MAP``.
    2. If no match, inspect the shebang (``#!``) line for interpreter hints.
    3. Fall back to ``'Texto Plano'``.

    Args:
        filepath: Absolute or relative path to the file.

    Returns:
        The detected language name.
    """
    ext = os.path.splitext(filepath)[1].lower()
    if ext in EXTENSION_MAP:
        return EXTENSION_MAP[ext]

    # Shebang fallback
    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            first_line = f.readline()
        if first_line.startswith("#!"):
            lower = first_line.lower()
            if "python" in lower:
                return "Python"
            if "bash" in lower or "/sh" in lower or " zsh" in lower:
                return "Shell"
            if "ruby" in lower:
                return "Ruby"
            if "perl" in lower:
                return "Perl"
            if "node" in lower:
                return "JavaScript"
    except (OSError, UnicodeDecodeError) as e:
        logger.warning("Could not read shebang from %s: %s", filepath, e)

    return "Texto Plano"
