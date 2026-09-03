
from __future__ import annotations

from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models

from astra.chunking.models import CodeChunk
from astra.config import Settings
from astra.errors import VectorStoreError
from astra.logging import get_logger

log = get_logger(__name__)


def upsert_chunks(
    client: QdrantClient,
    chunks: list[CodeChunk],
    vectors: list[list[float]],
    settings: Settings,
) -> None:
    
    if len(chunks) != len(vectors):
        raise ValueError(f"chunks/vectors length mismatch: {len(chunks)} vs {len(vectors)}")
    if not chunks:
        return

    from astra.vectorstore.schema import point_id

    points = [
        models.PointStruct(
            id=point_id(c.ingestion_id, c.repo, c.file_path, c.start_line, c.end_line),
            vector=v,
            payload=c.to_payload(),
        )
        for c, v in zip(chunks, vectors, strict=True)
    ]

    try:
        client.upsert(
            collection_name=settings.qdrant_collection,
            points=points,
            wait=False,
        )
        log.debug("upserted", n=len(points), collection=settings.qdrant_collection)
    except Exception as exc:
        raise VectorStoreError(f"Qdrant upsert failed: {exc}") from exc


def search(
    client: QdrantClient,
    query_vector: list[float],
    *,
    repo: str,
    ingestion_id: str,
    settings: Settings,
    query_text: str | None = None,
    top_k: int | None = None,
) -> list[dict[str, Any]]:
    
    top_k = top_k or settings.retrieval_top_k
    out: list[dict[str, Any]] = []
    seen_ids = set()
    # 1. Perform semantic Vector Search
    try:
        vector_response = client.query_points(
            collection_name=settings.qdrant_collection,
            query=query_vector,
            limit=top_k,
            score_threshold=settings.retrieval_score_threshold,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="ingestion_id",
                        match=models.MatchValue(value=ingestion_id),
                    ),
                ]
            ),
            with_payload=True,
        )
        for hit in vector_response.points:
            seen_ids.add(hit.id)
            out.append({
                "score": hit.score,
                **dict(hit.payload or {}),
            })
    except Exception as exc:
        raise VectorStoreError(f"Qdrant vector search failed: {exc}") from exc
    
    # 2. Perform Keyword (Tantivy) Full-Text Search
    if query_text:
        try:
            text_response, _ = client.scroll(
                collection_name=settings.qdrant_collection,
                scroll_filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="ingestion_id",
                            match=models.MatchValue(value=ingestion_id),
                        ),
                        models.FieldCondition(
                            key="content",
                            match=models.MatchText(text=query_text),
                        ),
                    ]
                ),
                limit=10,
                with_payload=True,
            )
            
            for point in text_response:
                if point.id not in seen_ids:
                    seen_ids.add(point.id)
                    out.append({
                        "score": 1.0,  # Assign a default high relevance score for exact keyword matches
                        **dict(point.payload or {}),
                    })
        except Exception as exc:
            log.warning("text_search_failed", error=str(exc))
    return out


def delete_repo(client: QdrantClient, repo: str, settings: Settings) -> int:
    try:
        client.delete(
            collection_name=settings.qdrant_collection,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="repo",
                            match=models.MatchValue(value=repo),
                        )
                    ]
                )
            ),
        )
        log.info("deleted_repo", repo=repo)
        return -1 
    except Exception as exc:
        raise VectorStoreError(f"Qdrant delete failed: {exc}") from exc


__all__ = ["delete_repo", "search", "upsert_chunks"]
