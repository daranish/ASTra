
"""Query endpoint — embed question, retrieve chunks, stream answer and sources."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from astra.api.deps import rag_dep
from astra.api.schemas import QueryRequest
from astra.rag.pipeline import RAGPipeline

router = APIRouter(prefix="/query", tags=["query"])


@router.post("/stream")
async def query_stream(
    payload: QueryRequest,
    rag: RAGPipeline = Depends(rag_dep),
) -> StreamingResponse:

    async def event_generator() -> AsyncIterator[str]:
        try:
            async for event in rag.answer_stream(
                repo_url=payload.repo,
                ingestion_id=payload.ingestion_id,
                question=payload.question,
            ):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as exc:
            # Stream the error cleanly to the frontend without crashing uvicorn
            error_event = {
                "type": "error",
                "message": str(exc)
            }
            yield f"data: {json.dumps(error_event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


__all__ = ["router"]