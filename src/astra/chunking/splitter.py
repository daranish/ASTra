
from __future__ import annotations

from pathlib import Path

from astra.chunking.models import CodeChunk
from astra.config import Settings
from astra.parsing.fallback import fallback_window_chunks, split_oversized
from astra.parsing.languages import detect_language, is_extractable
from astra.parsing.parser import extract_chunks


def chunk_file(path: Path, source: str, *, repo: str, ingestion_id: str, settings: Settings) -> list[CodeChunk]:
    file_path = str(path)
    language = detect_language(path)

    if language is None or not is_extractable(language):
        return fallback_window_chunks(
            source,
            file_path=file_path,
            repo=repo,
            ingestion_id=ingestion_id,
            language=language or "text",
            window_tokens=settings.window_tokens,
            overlap_tokens=settings.window_overlap,
        )

    try:
        chunks = extract_chunks(source, language, file_path=file_path, repo=repo, ingestion_id=ingestion_id)
    except Exception:
        return fallback_window_chunks(
            source,
            file_path=file_path,
            repo=repo,
            ingestion_id=ingestion_id,
            language=language,
            window_tokens=settings.window_tokens,
            overlap_tokens=settings.window_overlap,
        )

    out: list[CodeChunk] = []
    for c in chunks:
        if c.token_count > settings.max_chunk_tokens:
            out.extend(split_oversized(c, settings.max_chunk_tokens))
        else:
            out.append(c)

    if not out and source.strip():
        out.append(
            CodeChunk(
                repo=repo,
                ingestion_id=ingestion_id,
                file_path=file_path,
                language=language,
                symbol_name="<module>",
                symbol_kind="module",
                parent=None,
                start_line=1,
                end_line=source.count("\n") + 1,
                content=source,
                token_count=len(source) // 4,  # rough approximation
            )
        )
    return out


__all__ = ["chunk_file"]
