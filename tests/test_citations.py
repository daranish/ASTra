
from __future__ import annotations

from astra.rag.citations import hit_to_source


def test_hit_to_source_includes_all_fields():
    hit = {
        "score": 0.87,
        "file_path": "src/foo.py",
        "language": "python",
        "symbol_name": "add",
        "symbol_kind": "function",
        "parent": "Calculator",
        "start_line": 10,
        "end_line": 15,
        "content": "def add(self, a, b):\n    return a + b\n",
    }
    src = hit_to_source(hit)
    assert src["file_path"] == "src/foo.py"
    assert src["symbol_name"] == "add"
    assert src["symbol_kind"] == "function"
    assert src["parent"] == "Calculator"
    assert src["start_line"] == 10
    assert src["end_line"] == 15
    assert src["score"] == 0.87
    assert "def add" in src["snippet"]


def test_snippet_truncated_to_240_chars():
    long_content = "x = 1\n" * 200
    hit = {"content": long_content, "file_path": "x", "start_line": 1, "end_line": 100}
    src = hit_to_source(hit)
    assert len(src["snippet"]) <= 240


def test_snippet_replaces_newlines():
    hit = {"content": "line1\nline2\nline3", "file_path": "x"}
    src = hit_to_source(hit)
    assert "\n" not in src["snippet"]
    assert "line1" in src["snippet"]


def test_missing_fields_default_to_none():
    src = hit_to_source({})
    assert src["file_path"] is None
    assert src["score"] is None
