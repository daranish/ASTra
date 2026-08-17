
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

SymbolKind = Literal["function", "class", "method", "module", "block"]


@dataclass(frozen=True, slots=True)
class CodeChunk:

    repo: str
    ingestion_id: str
    file_path: str
    language: str
    symbol_name: str
    symbol_kind: SymbolKind
    parent: str | None
    start_line: int
    end_line: int
    content: str
    token_count: int
    chunk_id: str = field(default="")

    def __post_init__(self) -> None:
        if not self.chunk_id:
            object.__setattr__(
                self,
                "chunk_id",
                f"{self.repo}::{self.ingestion_id}::{self.file_path}::{self.start_line}::{self.end_line}",
            )

    def to_payload(self) -> dict:
        return {
            "repo": self.repo,
            "ingestion_id": self.ingestion_id,
            "file_path": self.file_path,
            "language": self.language,
            "symbol_name": self.symbol_name,
            "symbol_kind": self.symbol_kind,
            "parent": self.parent,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "content": self.content,
            "token_count": self.token_count,
        }
