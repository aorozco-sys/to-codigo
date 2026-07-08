"""Unit tests for language detection (extension-based and shebang fallback)."""

from __future__ import annotations

from to_codigo.core.language import detect_language, get_language_config, LANGUAGE_CONFIGS


# ---------------------------------------------------------------------------
# Extension-based detection
# ---------------------------------------------------------------------------

def test_python_extension():
    assert detect_language("foo.py") == "Python"


def test_javascript_extension():
    assert detect_language("app.js") == "JavaScript"


def test_typescript_extension():
    assert detect_language("app.ts") == "TypeScript"


def test_php_extension():
    assert detect_language("index.php") == "PHP"


def test_cpp_variants():
    assert detect_language("foo.cpp") == "C++"
    assert detect_language("foo.cc") == "C++"
    assert detect_language("foo.cxx") == "C++"


def test_case_insensitive_extension():
    assert detect_language("FILE.PY") == "Python"
    assert detect_language("App.JS") == "JavaScript"


def test_unknown_extension_falls_back(tmp_path):
    """File with unknown extension and no shebang -> 'Texto Plano'."""
    f = tmp_path / "data.xyz123"
    f.write_text("some content")
    assert detect_language(str(f)) == "Texto Plano"


# ---------------------------------------------------------------------------
# Shebang-based detection
# ---------------------------------------------------------------------------

def test_shebang_python(tmp_path):
    f = tmp_path / "myscript"
    f.write_text("#!/usr/bin/env python3\nprint('hi')\n")
    assert detect_language(str(f)) == "Python"


def test_shebang_bash(tmp_path):
    f = tmp_path / "deploy"
    f.write_text("#!/bin/bash\necho hi\n")
    assert detect_language(str(f)) == "Shell"


def test_shebang_node(tmp_path):
    f = tmp_path / "runme"
    f.write_text("#!/usr/bin/env node\nconsole.log('hi')\n")
    assert detect_language(str(f)) == "JavaScript"


def test_shebang_ruby(tmp_path):
    f = tmp_path / "script"
    f.write_text("#!/usr/bin/ruby\nputs 'hi'\n")
    assert detect_language(str(f)) == "Ruby"


def test_shebang_perl(tmp_path):
    f = tmp_path / "script2"
    f.write_text("#!/usr/bin/perl\nprint 'hi'\n")
    assert detect_language(str(f)) == "Perl"


# ---------------------------------------------------------------------------
# LanguageConfig registry
# ---------------------------------------------------------------------------

def test_php_config_has_all_three_comment_styles():
    """The PHP bug fix: config must include //, #, and /* */."""
    cfg = get_language_config("PHP")
    assert cfg is not None
    assert "//" in cfg.line_comments
    assert "#" in cfg.line_comments
    assert ("/*", "*/") in cfg.block_comment_pairs


def test_python_config_hash_only():
    cfg = get_language_config("Python")
    assert cfg is not None
    assert cfg.line_comments == ("#",)
    assert cfg.block_comment_pairs == ()


def test_unknown_language_returns_none():
    assert get_language_config("Brainfuck") is None


def test_all_configured_languages_present():
    """Every language from the counter requirement must have a config."""
    required = {
        "Python", "JavaScript", "TypeScript", "Java", "C#", "C", "C++",
        "Go", "Rust", "Ruby", "PHP", "Perl", "Shell", "Bash",
        "R", "MATLAB", "Swift", "Kotlin", "Scala", "Haskell",
        "Lua", "Dart", "Elixir",
    }
    configured = set(LANGUAGE_CONFIGS.keys())
    missing = required - configured
    assert not missing, f"Missing configs for: {missing}"
