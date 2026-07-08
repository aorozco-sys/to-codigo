# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-08

### Added
- Initial release of `to-codigo` as a standalone package.
- Data-driven comment detection for 40+ programming languages.
- Multiprocessing scanner for CPU-bound line counting.
- Strategy-pattern reporters: CSV, XLSX (styled Excel), JSON.
- Rich CLI with ASCII banner, progress bar, and color-coded results table.
- Full argparse CLI with `--format`, `--include-ext`, `--exclude-dirs`, `--workers`, and more.
- `.gitignore` support (via `pathspec` if available, `fnmatch` fallback).
- Shebang-based language detection fallback for extensionless scripts.
- Comprehensive test suite covering all comment families.
