# Contributing to to-codigo

Thank you for your interest in contributing! This document covers the basics.

## Development Setup

```bash
git clone https://github.com/Audithor/to-codigo.git
cd to-codigo
pip install -e ".[dev]"
```

## Running Tests

```bash
python -m pytest tests/ -v
```

## Code Style

- Python 3.10+ (uses `from __future__ import annotations`).
- Type hints everywhere.
- `dataclass(frozen=True)` for immutable data models.
- Strategy pattern for reporters, data-driven configs for language detection.
- Docstrings on every public function/class.

## Adding a New Language

1. Add the extension(s) to `EXTENSION_MAP` in `to_codigo/core/language.py`.
2. Add a `LanguageConfig` entry to `LANGUAGE_CONFIGS` with the correct comment syntax.
3. Add a test case in `tests/test_counter.py`.
4. Add a test case in `tests/test_language.py` for extension detection.

## Adding a New Reporter

1. Create a new class inheriting from `Reporter` in `to_codigo/core/reporter.py`.
2. Implement the `generate()` method.
3. Register it in the `REPORTERS` dict.
4. Add the format choice to the CLI `--format` argument in `__main__.py`.

## Pull Requests

1. Fork the repo and create a feature branch.
2. Write tests for your changes.
3. Ensure all tests pass: `python -m pytest tests/ -v`.
4. Keep commits focused and well-described.
