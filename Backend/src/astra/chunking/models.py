
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

    def to_embedding_text(self) -> str:
        """
        Language-agnostic chunk enrichment. Builds a natural language metadata
        header containing path location, structural depth, and symbol metadata.
        """
        import pathlib

        p = pathlib.Path(self.file_path)
        filename = p.name
        
        # Calculate depth to distinguish root-level entry files from deep helper files
        parts_count = len(p.parts)
        is_root_level = parts_count <= 2
        location_str = "root directory of project" if is_root_level else f"folder `{p.parent.name}`"

        header_components: list[str] = [
            f"Source file: `{filename}` in {location_str}.",
            f"Programming language: {self.language}.",
            f"Code construct: {self.symbol_kind} `{self.symbol_name}`.",
        ]

        if self.parent:
            header_components.append(f"Parent class/scope: `{self.parent}`.")

        if is_root_level and self.symbol_kind in ("module", "block"):
            header_components.append("This is top-level script/module code in the repository root.")

        header = " ".join(header_components)
        return f"{header}\n\n```{self.language}\n{self.content.strip()}\n```"