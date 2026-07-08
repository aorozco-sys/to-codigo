"""Unit tests for the line-counting engine.

Covers the PHP ``#``-comment bug fix, plus representative languages from
each comment family (hash, C-style, block-only, ``--``-style, Lua, Haskell).
"""

from __future__ import annotations

from to_codigo.core.counter import count_lines


# ---------------------------------------------------------------------------
# PHP -- the critical bug fix
# ---------------------------------------------------------------------------

def test_php_hash_comment(tmp_path):
    """PHP ``#`` comments MUST be counted (the original bug: dead elif)."""
    f = tmp_path / "test.php"
    f.write_text(
        "# This is a hash comment\n"
        "// This is a slash comment\n"
        "/* This is a block comment */\n"
        "$x = 1;\n"
        "\n"
    )
    total, code, comment, blank = count_lines(str(f), "PHP")
    assert blank == 1
    assert code == 1
    assert comment == 3  # all three comment styles counted
    assert total == 5


def test_php_multiline_block_comment(tmp_path):
    """PHP multi-line block comments span multiple lines correctly."""
    f = tmp_path / "block.php"
    f.write_text(
        "/*\n"
        " * Multi-line block\n"
        " */\n"
        "$x = 2;\n"
    )
    total, code, comment, blank = count_lines(str(f), "PHP")
    assert code == 1
    assert comment == 3
    assert total == 4


def test_php_inline_code_before_block(tmp_path):
    """A line with code followed by a block-open is counted as code."""
    f = tmp_path / "inline.php"
    f.write_text(
        "$x = 1; /* opens a block\n"
        "still in block\n"
        "*/\n"
        "$y = 2;\n"
    )
    total, code, comment, blank = count_lines(str(f), "PHP")
    assert code == 2  # line 1 (code+block-open), line 4
    assert comment == 2  # lines 2-3 (inside block)


# ---------------------------------------------------------------------------
# Python -- hash comments
# ---------------------------------------------------------------------------

def test_python_comments(tmp_path):
    f = tmp_path / "test.py"
    f.write_text(
        "# Full line comment\n"
        "x = 1  # inline comment\n"
        "\n"
        "def foo():\n"
        "    return 42\n"
    )
    total, code, comment, blank = count_lines(str(f), "Python")
    assert blank == 1
    assert comment == 1  # only the full-line comment
    assert code == 3     # inline-comment line counts as code
    assert total == 5


def test_python_blank_and_code_only(tmp_path):
    f = tmp_path / "clean.py"
    f.write_text("x = 1\n\ny = 2\n")
    total, code, comment, blank = count_lines(str(f), "Python")
    assert code == 2
    assert blank == 1
    assert comment == 0
    assert total == 3


# ---------------------------------------------------------------------------
# JavaScript / TypeScript -- C-style
# ---------------------------------------------------------------------------

def test_javascript_comments(tmp_path):
    f = tmp_path / "test.js"
    f.write_text(
        "// line comment\n"
        "/* block comment */\n"
        "const x = 1;\n"
        "/*\n"
        "  multi\n"
        "  line\n"
        "*/\n"
        "\n"
    )
    total, code, comment, blank = count_lines(str(f), "JavaScript")
    assert blank == 1
    assert code == 1
    assert comment == 6  # // line, /* single */, 4 lines of multi-line block
    assert total == 8


def test_typescript_comments(tmp_path):
    f = tmp_path / "test.ts"
    f.write_text(
        "// TS comment\n"
        "let x: number = 42;\n"
    )
    total, code, comment, blank = count_lines(str(f), "TypeScript")
    assert code == 1
    assert comment == 1


# ---------------------------------------------------------------------------
# Java -- C-style block
# ---------------------------------------------------------------------------

def test_java_multiline_block(tmp_path):
    f = tmp_path / "Test.java"
    f.write_text(
        "/**\n"
        " * Javadoc comment\n"
        " */\n"
        "public class Test {\n"
        "}\n"
    )
    total, code, comment, blank = count_lines(str(f), "Java")
    assert code == 2
    assert comment == 3  # Javadoc block


# ---------------------------------------------------------------------------
# C -- C-style
# ---------------------------------------------------------------------------

def test_c_comments(tmp_path):
    f = tmp_path / "main.c"
    f.write_text(
        "#include <stdio.h>\n"   # code (no comment in C)
        "// comment\n"
        "int main() {\n"
        "    /* inline */ return 0;\n"
        "}\n"
    )
    total, code, comment, blank = count_lines(str(f), "C")
    assert code == 4
    assert comment == 1


# ---------------------------------------------------------------------------
# Go -- C-style
# ---------------------------------------------------------------------------

def test_go_comments(tmp_path):
    f = tmp_path / "main.go"
    f.write_text(
        "package main\n"
        "// comment\n"
        "/* block */\n"
    )
    total, code, comment, blank = count_lines(str(f), "Go")
    assert code == 1
    assert comment == 2


# ---------------------------------------------------------------------------
# Ruby -- hash
# ---------------------------------------------------------------------------

def test_ruby_comments(tmp_path):
    f = tmp_path / "test.rb"
    f.write_text(
        "# comment\n"
        "puts 'hello'\n"
    )
    total, code, comment, blank = count_lines(str(f), "Ruby")
    assert code == 1
    assert comment == 1


# ---------------------------------------------------------------------------
# Shell / Bash -- hash
# ---------------------------------------------------------------------------

def test_shell_comments(tmp_path):
    f = tmp_path / "test.sh"
    f.write_text(
        "#!/bin/bash\n"
        "# comment\n"
        "echo hello\n"
    )
    total, code, comment, blank = count_lines(str(f), "Shell")
    assert code == 1  # echo (shebang #! starts with # -> comment)
    assert comment == 2  # shebang + comment


# ---------------------------------------------------------------------------
# Haskell -- -- + {- -}
# ---------------------------------------------------------------------------

def test_haskell_block_comment(tmp_path):
    f = tmp_path / "test.hs"
    f.write_text(
        "-- line comment\n"
        "{- block\n"
        "comment -}\n"
        "main = putStrLn \"hi\"\n"
    )
    total, code, comment, blank = count_lines(str(f), "Haskell")
    assert code == 1
    assert comment == 3  # -- line + 2 lines of block


# ---------------------------------------------------------------------------
# Lua -- -- + --[[ ]]
# ---------------------------------------------------------------------------

def test_lua_block_comment(tmp_path):
    f = tmp_path / "test.lua"
    f.write_text(
        "-- line comment\n"
        "--[[ block\n"
        "comment ]]\n"
        "print('hi')\n"
    )
    total, code, comment, blank = count_lines(str(f), "Lua")
    assert code == 1
    assert comment == 3


# ---------------------------------------------------------------------------
# MATLAB -- % + %{ %}
# ---------------------------------------------------------------------------

def test_matlab_comments(tmp_path):
    f = tmp_path / "test.m"
    f.write_text(
        "% comment\n"
        "x = 5;\n"
    )
    total, code, comment, blank = count_lines(str(f), "MATLAB")
    assert code == 1
    assert comment == 1


# ---------------------------------------------------------------------------
# Rust -- C-style
# ---------------------------------------------------------------------------

def test_rust_comments(tmp_path):
    f = tmp_path / "main.rs"
    f.write_text(
        "// comment\n"
        "/* block */\n"
        "fn main() {}\n"
    )
    total, code, comment, blank = count_lines(str(f), "Rust")
    assert code == 1
    assert comment == 2


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_empty_file(tmp_path):
    f = tmp_path / "empty.py"
    f.write_text("")
    total, code, comment, blank = count_lines(str(f), "Python")
    assert (total, code, comment, blank) == (0, 0, 0, 0)


def test_only_blank_lines(tmp_path):
    f = tmp_path / "blank.py"
    f.write_text("\n\n\n")
    total, code, comment, blank = count_lines(str(f), "Python")
    assert blank == 3
    assert code == 0


def test_plain_text_no_config(tmp_path):
    """Languages without a comment config should count every non-blank line as code."""
    f = tmp_path / "notes.txt"
    f.write_text("hello\nworld\n\n")
    total, code, comment, blank = count_lines(str(f), "Texto Plano")
    assert code == 2
    assert blank == 1
    assert comment == 0
