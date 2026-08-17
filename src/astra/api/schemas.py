
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    repo_url: str = Field(
        ...,
        description="GitHub repo URL (https://github.com/<owner>/<repo>)",
        examples=["https://github.com/pallets/flask"],
    )


class IngestAcceptedResponse(BaseModel):
    job_id: str
    repo_url: str
    status: str = "queued"


class JobStatusResponse(BaseModel):
    job_id: str
    repo_url: str
    status: str
    started_at: float
    finished_at: float | None = None
    files_total: int = 0
    files_done: int = 0
    chunks_total: int = 0
    chunks_indexed: int = 0
    error: str | None = None


class QueryRequest(BaseModel):
    repo: str = Field(
        ...,
        description="GitHub repo URL that was previously ingested",
        examples=["https://github.com/pallets/flask"],
    )
    question: str = Field(..., min_length=1, max_length=4000)


class Source(BaseModel):
    file_path: str | None = None
    language: str | None = None
    symbol_name: str | None = None
    symbol_kind: str | None = None
    parent: str | None = None
    start_line: int | None = None
    end_line: int | None = None
    score: float | None = None
    snippet: str | None = None


class QueryResponse(BaseModel):
    answer: str
    sources: list[Source]


class HealthResponse(BaseModel):
    status: str = "ok"
    qdrant: bool
    has_deepseek_key: bool
    has_google_key: bool
    details: dict[str, Any] = Field(default_factory=dict)
