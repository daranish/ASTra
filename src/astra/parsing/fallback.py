
from __future__ import annotations

from dataclasses import replace

from astra.chunking.models import CodeChunk
from astra.chunking.tokens import count_tokens, split_token_budget


def split_oversized(chunk: CodeChunk, max_tokens: int) -> list[CodeChunk]:
    
    if chunk.token_count <= max_tokens:
        return [chunk]

    budget = max(64, max_tokens - 50)  # leave headroom
    pieces = split_token_budget(chunk.content, budget)
    if not pieces:
        return [chunk]

    n = len(pieces)
    line_span = max(1, chunk.end_line - chunk.start_line)
    out: list[CodeChunk] = []
    for i, text in enumerate(pieces):
        start_line = chunk.start_line + (line_span * i) // n
        end_line = chunk.start_line + (line_span * (i + 1)) // n
        out.append(
            replace(
                chunk,
                content=text,
                start_line=start_line,
                end_line=end_line,
                token_count=count_tokens(text),
                symbol_kind="block",
            )
        )
    return out


def fallback_window_chunks(
    source: str,
    *,
    file_path: str,
    repo: str,
    ingestion_id: str,
    language: str,
    window_tokens: int,
    overlap_tokens: int,
) -> list[CodeChunk]:
    lines = source.splitlines(keepends=True)
    if not lines:
        return []

    chunks: list[CodeChunk] = []
    current: list[str] = []
    current_tokens = 0
    start_line = 1
    budget = window_tokens

    for i, line in enumerate(lines, start=1):
        line_tokens = count_tokens(line) or 1
        if current_tokens + line_tokens > budget and current:
            content = "".join(current)
            chunks.append(
                CodeChunk(
                    repo=repo,
                    ingestion_id=ingestion_id,
                    file_path=file_path,
                    language=language or "text",
                    symbol_name=f"lines_{start_line}_{i - 1}",
                    symbol_kind="block",
                    parent=None,
                    start_line=start_line,
                    end_line=i - 1,
                    content=content,
                    token_count=count_tokens(content),
                )
            )
            keep_lines: list[str] = []
            kept_tokens = 0
            for prev in reversed(current):
                t = count_tokens(prev) or 1
                if kept_tokens + t > overlap_tokens:
                    break
                keep_lines.insert(0, prev)
                kept_tokens += t
            current = keep_lines
            current_tokens = kept_tokens
            start_line = i - len(keep_lines)

        current.append(line)
        current_tokens += line_tokens

    if current:
        content = "".join(current)
        chunks.append(
            CodeChunk(
                repo=repo,
                ingestion_id=ingestion_id,
                file_path=file_path,
                language=language or "text",
                symbol_name=f"lines_{start_line}_{len(lines)}",
                symbol_kind="block",
                parent=None,
                start_line=start_line,
                end_line=len(lines),
                content=content,
                token_count=count_tokens(content),
            )
        )

    return chunks
