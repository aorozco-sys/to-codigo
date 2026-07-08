"""Data models for to-codigo.

Defines the core data structures used across the package:
``FileInfo`` represents a single scanned source file, ``LanguageStats``
aggregates metrics per programming language, and ``TodoItem`` captures
a single TODO/FIXME/HACK/NOTE marker occurrence.

Audit tracking models: ``AuditEntry`` and ``AuditState`` persist which
files have been reviewed during a security code audit.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


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
        audit_status: Audit status computed from previous report comparison.
            One of: ``"Auditado"``, ``"Pendiente"``, ``"Modificado"``, ``"Nuevo"``.
            Default ``"Pendiente"`` when no audit data is available.
        audit_marked: What the auditor set in the previous report (``"Si"`` or ``"No"``).
            Used as the value for the ``Auditado`` column in output reports.
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
    audit_status: str = "Pendiente"
    audit_marked: str = "No"


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


# ---------------------------------------------------------------------------
# Audit tracking models
# ---------------------------------------------------------------------------

@dataclass
class FileChangeStatus:
    """Describes whether a file changed since the previous report.

    Attributes:
        status: ``"Auditado"`` (audited+unchanged), ``"Pendiente"`` (unaudited+unchanged),
            ``"Modificado"`` (file changed since last audit), or ``"Nuevo"`` (not in previous report).
        audited: ``"Si"`` or ``"No"`` — the audit mark from the previous report.
        previous_size: File size in bytes from the previous report.
        previous_mtime: Modification timestamp string from the previous report.
    """
    status: str
    audited: str
    previous_size: int = 0
    previous_mtime: str = ""


@dataclass
class AuditDiff:
    """Result of comparing current scan against previous report.

    Attributes:
        audited_unchanged: Files that were ``"Si"`` and didn't change.
        audited_modified: Files that were ``"Si"`` but the file changed.
        pending_unchanged: Files that were ``"No"`` and didn't change.
        new_files: Files not in previous report.
        removed_files: Files in previous but not in current.
        changes: Mapping of absolute path to :class:`FileChangeStatus`.
    """
    audited_unchanged: int = 0
    audited_modified: int = 0
    pending_unchanged: int = 0
    new_files: int = 0
    removed_files: int = 0
    changes: dict[str, FileChangeStatus] = field(default_factory=dict)

    def determine_status(
        self,
        filepath: str,
        current_size: int = 0,
        current_mtime: str = "",
    ) -> str:
        """Return the audit status for *filepath*.

        Returns one of: ``"Auditado"``, ``"Pendiente"``, ``"Modificado"``, ``"Nuevo"``.
        """
        status = self.changes.get(filepath)
        if status is None:
            return "Nuevo"
        return status.status


@dataclass
class AuditEntry:
    """Audit state for a single file.

    Attributes:
        filepath: Absolute filesystem path (used as the key in AuditState).
        audited: Whether this file has been marked as audited.
        auditor: Name of the person who audited the file.
        audit_date: Timestamp string ``YYYY-MM-DD HH:MM``.
        notes: Free-text notes left by the auditor.
    """

    filepath: str
    audited: bool = False
    auditor: str = ""
    audit_date: str = ""
    notes: str = ""


@dataclass
class AuditState:
    """Persistent audit tracking state across scans.

    Attributes:
        entries: Mapping of absolute file path to :class:`AuditEntry`.
        last_updated: Timestamp of the last modification.
    """

    entries: dict[str, AuditEntry] = field(default_factory=dict)
    last_updated: str = ""

    def is_audited(self, filepath: str) -> bool:
        """Return ``True`` if *filepath* is marked as audited."""
        return self.entries.get(filepath, AuditEntry(filepath=filepath)).audited

    def get_entry(self, filepath: str) -> AuditEntry:
        """Return the :class:`AuditEntry` for *filepath* (or a default)."""
        return self.entries.get(filepath, AuditEntry(filepath=filepath))

    def mark(
        self,
        filepath: str,
        audited: bool = True,
        auditor: str = "",
        notes: str = "",
    ) -> None:
        """Mark *filepath* as audited (or unaudited) with optional metadata."""
        entry = self.entries.get(filepath, AuditEntry(filepath=filepath))
        entry.audited = audited
        if auditor:
            entry.auditor = auditor
        if notes:
            entry.notes = notes
        entry.audit_date = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.entries[filepath] = entry
        self.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M")

    def stats(self, files: list[FileInfo]) -> dict:
        """Return audit statistics for a list of scanned files."""
        total_loc = sum(f.code_lines for f in files)
        audited_files = [f for f in files if self.is_audited(f.absolute_path)]
        audited_loc = sum(f.code_lines for f in audited_files)
        unaudited_loc = total_loc - audited_loc
        return {
            "total_files": len(files),
            "audited_files": len(audited_files),
            "unaudited_files": len(files) - len(audited_files),
            "total_loc": total_loc,
            "audited_loc": audited_loc,
            "unaudited_loc": unaudited_loc,
            "pct_audited": (audited_loc / total_loc * 100) if total_loc > 0 else 0,
            "pct_files_audited": (
                len(audited_files) / len(files) * 100 if files else 0
            ),
        }
