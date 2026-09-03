
from __future__ import annotations

import tiktoken

_ENCODER: tiktoken.Encoding | None = None


def _get_encoder() -> tiktoken.Encoding:
    global _ENCODER
    if _ENCODER is None:
        _ENCODER = tiktoken.get_encoding("cl100k_base")
    return _ENCODER


def count_tokens(text: str) -> int:
    return len(_get_encoder().encode(text))


def split_token_budget(text: str, budget: int) -> list[str]:
    tokens = _get_encoder().encode(text)
    chunks: list[str] = []
    decoder = _get_encoder().decode
    for i in range(0, len(tokens), budget):
        chunks.append(decoder(tokens[i : i + budget]))
    return chunks
