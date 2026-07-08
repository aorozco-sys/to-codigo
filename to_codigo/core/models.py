"""Data models for to-codigo.

Defines the core data structures used across the package:
``FileInfo`` represents a single scanned source file, ``LanguageStats``
aggregates metrics per programming language, and ``TodoItem`` captures
a single TODO/FIXME/HACK/NOTE marker occurrence.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FileInfo:
    """Immutable record describing a single source file and its metrics.

    Attributes:
        absolute_path: Fully-qualified filesystem path.
        relative_path: Directory path relative to the scan root.
        filename: Base name of the file (no directory).
        language: Detected programming language name.
        size_bytes: File size in bytes.
        modified_at: Last-modified timestamp as ``YYYY-MM-DD HH:MM:SS``.
        total_lines: Total number of lines in the file.
        code_lines: Number of lines containing code.
        comment_lines: Number of lines that are comments.
        blank_lines: Number of blank / whitespace-only lines.
        todos: Number of TODO markers found.
        fixmes: Number of FIXME/BUG markers found.
        hacks: Number of HACK/XXX markers found.
        notes: Number of NOTE markers found.
    """

    absolute_path: str
    relative_path: str
    filename: str
    language: str
    size_bytes: int
    modified_at: str
    total_lines: int
    code_lines: int
    comment_lines: int
    blank_lines: int
    todos: int = 0
    fixmes: int = 0
    hacks: int = 0
    notes: int = 0


@dataclass(frozen=True)
class TodoItem:
    """A single TODO/FIXME/HACK/XXX/BUG/NOTE marker occurrence.

    Attributes:
        filepath: Path to the source file.
        line_number: 1-based line number where the marker appears.
        marker: The marker keyword (TODO, FIXME, HACK, XXX, BUG, NOTE).
        text: The descriptive text following the marker.
    """

    filepath: str
    line_number: int
    marker: str
    text: str


@dataclass
class LanguageStats:
    """Mutable accumulator for per-language aggregate metrics.

    Attributes:
        files: Number of files for this language.
        total_code_lines: Sum of code lines across all files.
        total_comment_lines: Sum of comment lines.
        total_blank_lines: Sum of blank lines.
        total_lines: Grand total of all lines.
        total_todos: Sum of TODO markers.
        total_fixmes: Sum of FIXME/BUG markers.
        total_hacks: Sum of HACK/XXX markers.
        total_notes: Sum of NOTE markers.
    """

    files: int = 0
    total_code_lines: int = 0
    total_comment_lines: int = 0
    total_blank_lines: int = 0
    total_lines: int = 0
    total_todos: int = 0
    total_fixmes: int = 0
    total_hacks: int = 0
    total_notes: int = 0

    def add(self, info: FileInfo) -> None:
        """Merge a single ``FileInfo`` into this accumulator."""
        self.files += 1
        self.total_code_lines += info.code_lines
        self.total_comment_lines += info.comment_lines
        self.total_blank_lines += info.blank_lines
        self.total_lines += info.total_lines
        self.total_todos += info.todos
        self.total_fixmes += info.fixmes
        self.total_hacks += info.hacks
        self.total_notes += info.notes


@dataclass
class ScanResult:
    """Aggregate result of a directory scan.

    Attributes:
        files: List of ``FileInfo`` for all processed (text) files.
        stats: Per-language statistics dict.
        skipped_binary: Count of binary files that were skipped.
        skipped_errors: Count of files skipped due to errors.
    """

    files: list[FileInfo]
    stats: dict[str, "LanguageStats"]
    skipped_binary: int = 0
    skipped_errors: int = 0
