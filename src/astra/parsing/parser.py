
from __future__ import annotations

from dataclasses import dataclass

from tree_sitter_language_pack import ProcessConfig, process

from astra.chunking.models import CodeChunk
from astra.chunking.tokens import count_tokens
from astra.parsing.languages import pack_kind_to_ours


@dataclass(frozen=True, slots=True)
class Span:

    start_byte: int
    end_byte: int
    start_line: int
    end_line: int

    def to_1indexed(self) -> tuple[int, int]:
        return (self.start_line + 1, self.end_line + 1)


def _split_lines(text: str) -> list[str]:
    return text.split("\n")


def _slice_lines(source: str, start_line: int, end_line: int) -> str:
    lines = _split_lines(source)
    return "\n".join(lines[start_line : end_line + 1])


def _symbol_chunks(source: str, language: str, file_path: str, repo: str, ingestion_id: str) -> list[CodeChunk]:
    config = ProcessConfig(language=language, symbols=True)
    result = process(source, config)
    out: list[CodeChunk] = []
    for sym in result.symbols:
        kind_name = str(sym.kind)  # e.g. "Function", "Class"
        ours = pack_kind_to_ours(kind_name)
        if ours is None:
            continue
        span = sym.span
        start_l, end_l = span.start_line, span.end_line
        content = _slice_lines(source, start_l, end_l)
        out.append(
            CodeChunk(
                repo=repo,
                ingestion_id=ingestion_id,
                file_path=file_path,
                language=language,
                symbol_name=sym.name or "<anonymous>",
                symbol_kind=ours,  # type: ignore[arg-type]
                parent=None,
                start_line=start_l + 1,
                end_line=end_l + 1,
                content=content,
                token_count=count_tokens(content),
            )
        )
    return out


def _structure_chunks(source: str, language: str, file_path: str, repo: str, ingestion_id: str) -> list[CodeChunk]:

    config = ProcessConfig(language=language, structure=True)
    result = process(source, config)
    out: list[CodeChunk] = []

    def visit(item, parent_name: str | None) -> None:
        kind_name = str(item.kind)  # e.g. "Function", "Class"
        ours = pack_kind_to_ours(kind_name)
        if ours is not None and item.name:
            span = item.span
            start_l, end_l = span.start_line, span.end_line
            content = _slice_lines(source, start_l, end_l)
            out.append(
                CodeChunk(
                    repo=repo,
                    ingestion_id=ingestion_id,
                    file_path=file_path,
                    language=language,
                    symbol_name=item.name,
                    symbol_kind=ours,  # type: ignore[arg-type]
                    parent=parent_name,
                    start_line=start_l + 1,
                    end_line=end_l + 1,
                    content=content,
                    token_count=count_tokens(content),
                )
            )
        for child in item.children or []:
            visit(child, item.name if ours is not None else parent_name)

    for top in result.structure:
        visit(top, None)
    return out


def extract_chunks(
    source: str, language: str, ingestion_id: str, *, file_path: str = "", repo: str = ""
) -> list[CodeChunk]:

    try:
        config = ProcessConfig(language=language, structure=True)
        result = process(source, config)
    except Exception:
        return []
    if result.structure:
        return _structure_chunks(source, language, file_path, repo, ingestion_id)
    return _symbol_chunks(source, language, file_path, repo, ingestion_id)


def parse(source: str, language: str) -> object:
    return process(source, ProcessConfig(language=language, structure=True, symbols=True))


__all__ = ["Span", "extract_chunks", "parse"]
