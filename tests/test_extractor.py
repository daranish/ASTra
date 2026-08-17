
from __future__ import annotations

from astra.parsing.parser import extract_chunks


def test_python_function_extraction():
    src = "def add(a, b):\n    return a + b\n"
    chunks = extract_chunks(src, "python", file_path="m.py", repo="r")
    assert len(chunks) >= 1
    fn = next(c for c in chunks if c.symbol_name == "add")
    assert fn.symbol_kind == "function"
    assert fn.start_line == 1
    assert fn.end_line == 2
    assert "def add" in fn.content


def test_python_class_with_method():
    src = (
        "class Calc:\n"
        "    def add(self, a, b):\n"
        "        return a + b\n"
        "    def sub(self, a, b):\n"
        "        return a - b\n"
    )
    chunks = extract_chunks(src, "python", file_path="m.py", repo="r")
    calc = next(c for c in chunks if c.symbol_name == "Calc")
    assert calc.symbol_kind == "class"
    add = next(c for c in chunks if c.symbol_name == "add")
    assert add.symbol_kind in ("function", "method")
    children = [c for c in chunks if c.parent == "Calc"]
    assert len(children) >= 1


def test_javascript_class_with_methods():
    src = (
        "class User {\n"
        "  constructor(name) { this.name = name; }\n"
        "  sayHi() { return this.name; }\n"
        "}\n"
    )
    chunks = extract_chunks(src, "javascript", file_path="u.js", repo="r")
    user = next(c for c in chunks if c.symbol_name == "User")
    assert user.symbol_kind == "class"
    say_hi = next(c for c in chunks if c.symbol_name == "sayHi")
    assert say_hi.parent == "User"


def test_go_method_on_struct():
    src = (
        "package main\n"
        "type Calculator struct{}\n"
        "func (c *Calculator) Add(a, b int) int { return a + b }\n"
    )
    chunks = extract_chunks(src, "go", file_path="m.go", repo="r")
    names = {c.symbol_name for c in chunks}
    assert "Add" in names


def test_rust_function_and_impl():
    src = "fn add(a: i32, b: i32) -> i32 { a + b }\n"
    chunks = extract_chunks(src, "rust", file_path="m.rs", repo="r")
    assert any(c.symbol_name == "add" for c in chunks)


def test_unsupported_language_returns_empty():
    chunks = extract_chunks("hello", "brainfuck", file_path="x.bf", repo="r")
    assert chunks == []


def test_repo_and_file_path_stamped():
    chunks = extract_chunks("def x(): pass\n", "python", file_path="f.py", repo="r")
    for c in chunks:
        assert c.repo == "r"
        assert c.file_path == "f.py"
