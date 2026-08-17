"""/query endpoint — embed question, retrieve chunks, answer with DeepSeek."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from astra.api.deps import rag_dep
from astra.api.schemas import QueryRequest, QueryResponse, Source
from astra.rag.pipeline import RAGPipeline

router = APIRouter(prefix="/query", tags=["query"])


@router.post("", response_model=QueryResponse)
async def query(
    payload: QueryRequest,
    rag: RAGPipeline = Depends(rag_dep),
) -> QueryResponse:
    """Answer a question about a previously-ingested repo."""
    result = await rag.answer(payload.repo, payload.question)
    return QueryResponse(
        answer=result.answer,
        sources=[Source(**s) for s in result.sources],
    )


__all__ = ["router"]
