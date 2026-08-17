
from __future__ import annotations

import hashlib
import uuid

from qdrant_client import QdrantClient
from qdrant_client.http import models

from astra.config import Settings
from astra.errors import VectorStoreError
from astra.logging import get_logger

log = get_logger(__name__)


def point_id(ingestion_id: str, repo: str, file_path: str, start_line: int, end_line: int) -> str:
   
    raw = f"{ingestion_id}::{repo}::{file_path}::{start_line}::{end_line}"
    digest = hashlib.sha1(raw.encode("utf-8")).digest()
    return str(uuid.UUID(bytes=digest[:16]))


def ensure_collection(client: QdrantClient, settings: Settings) -> None:
    
    name = settings.qdrant_collection
    if client.collection_exists(name):
        log.debug("collection_exists", name=name)
        return

    try:
        client.create_collection(
            collection_name=name,
            vectors_config=models.VectorParams(
                size=settings.embedding_dims,
                distance=models.Distance.COSINE,
                hnsw_config=models.HnswConfigDiff(m=16, ef_construct=128),
            ),
            optimizers_config=models.OptimizersConfigDiff(default_segment_number=2),
        )
        log.info("collection_created", name=name, dims=settings.embedding_dims)
    except Exception as exc:
        raise VectorStoreError(f"Failed to create collection '{name}': {exc}") from exc

    for field in ("repo", "ingestion_id", "language", "file_path", "symbol_kind"):
        try:
            client.create_payload_index(
                collection_name=name,
                field_name=field,
                field_schema=models.PayloadSchemaType.KEYWORD,
            )
        except Exception as exc:
            log.warning("payload_index_failed", field=field, error=str(exc))


__all__ = ["ensure_collection", "point_id"]
