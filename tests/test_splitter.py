"""Tests for the oversized-chunk splitter."""

from __future__ import annotations

from astra.chunking.models import CodeChunk
from astra.parsing.fallback import split_oversized


def _make_chunk(content: str, token_count: int) -> CodeChunk:
    return CodeChunk(
        repo="r",
        file_path="f.py",
        language="python",
        symbol_name="big",
        symbol_kind="function",
        parent=None,
        start_line=1,
        end_line=100,
        content=content,
        token_count=token_count,
    )


def test_split_under_limit_returns_unchanged():
    chunk = _make_chunk("def f(): return 1", token_count=5)
    out = split_oversized(chunk, max_tokens=100)
    assert out == [chunk]


def test_split_oversized_produces_multiple_chunks():
    big = "def f():\n    x = 1\n" * 200  # ~1200 tokens
    chunk = _make_chunk(big, token_count=1200)
    out = split_oversized(chunk, max_tokens=300)
    assert len(out) > 1
    # All sub-chunks should be smaller than the original
    for c in out:
        assert c.token_count <= 350  # some headroom
    # All should be marked as "block" since they were split
    for c in out:
        assert c.symbol_kind == "block"


def test_split_preserves_metadata():
    big = "x = 1\n" * 1000
    chunk = _make_chunk(big, token_count=1000)
    out = split_oversized(chunk, max_tokens=200)
    for c in out:
        assert c.repo == "r"
        assert c.file_path == "f.py"
        assert c.language == "python"
        # Line numbers should be within the original range
        assert 1 <= c.start_line <= c.end_line <= 100


def test_fallback_window_chunks_handles_empty():
    from astra.parsing.fallback import fallback_window_chunks

    assert (
        fallback_window_chunks(
            "", file_path="f", repo="r", language="text", window_tokens=100, overlap_tokens=10
        )
        == []
    )
