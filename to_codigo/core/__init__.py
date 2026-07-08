"""Core package — models, detection, counting, scanning, and reporting."""

from to_codigo.core.models import FileInfo, LanguageStats
from to_codigo.core.language import (
    LanguageConfig,
    LANGUAGE_CONFIGS,
    detect_language,
    get_language_config,
)
from to_codigo.core.counter import count_lines
from to_codigo.core.scanner import scan_directory, compute_stats
from to_codigo.core.reporter import Reporter, CSVReporter, XLSXReporter, JSONReporter, REPORTERS

__all__ = [
    "FileInfo",
    "LanguageStats",
    "LanguageConfig",
    "LANGUAGE_CONFIGS",
    "detect_language",
    "get_language_config",
    "count_lines",
    "scan_directory",
    "compute_stats",
    "Reporter",
    "CSVReporter",
    "XLSXReporter",
    "JSONReporter",
    "REPORTERS",
]
