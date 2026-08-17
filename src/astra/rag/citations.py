
from __future__ import annotations

from typing import Any


def _truncate(text: str, n: int = 240) -> str:
    text = text.strip().replace("\n", " ")
    return text if len(text) <= n else text[: n - 1] + "…"


def hit_to_source(hit: dict[str, Any]) -> dict[str, Any]:
    """Map a raw Qdrant hit (with payload) to a citation-friendly source dict."""
    return {
        "file_path": hit.get("file_path"),
        "language": hit.get("language"),
        "symbol_name": hit.get("symbol_name"),
        "symbol_kind": hit.get("symbol_kind"),
        "parent": hit.get("parent"),
        "start_line": hit.get("start_line"),
        "end_line": hit.get("end_line"),
        "score": hit.get("score"),
        "snippet": _truncate(hit.get("content", "")),
    }


__all__ = ["hit_to_source"]
