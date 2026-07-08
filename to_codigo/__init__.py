"""to-codigo — modular code analysis and inventory tool.

A clean, testable package with:

- Data-driven comment detection (no hardcoded if/elif chains).
- Multiprocessing for CPU-bound line counting.
- Strategy-pattern reporters (CSV, XLSX, JSON).
- Full type hints and structured logging.
"""

from to_codigo.core.models import FileInfo, LanguageStats
from to_codigo.core.language import detect_language, LanguageConfig, LANGUAGE_CONFIGS
from to_codigo.core.counter import count_lines
from to_codigo.core.scanner import scan_directory
from to_codigo.core.reporter import Reporter, CSVReporter, XLSXReporter, JSONReporter, REPORTERS

__version__ = "1.0.0"

__all__ = [
    "FileInfo",
    "LanguageStats",
    "LanguageConfig",
    "LANGUAGE_CONFIGS",
    "detect_language",
    "count_lines",
    "scan_directory",
    "Reporter",
    "CSVReporter",
    "XLSXReporter",
    "JSONReporter",
    "REPORTERS",
]
