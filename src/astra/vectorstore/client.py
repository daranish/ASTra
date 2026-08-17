
from __future__ import annotations

from qdrant_client import QdrantClient

from astra.config import Settings


def make_client(settings: Settings) -> QdrantClient:
    
    if settings.qdrant_url:
        return QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key,
        )
    if settings.qdrant_persist_path:
        path = settings.qdrant_persist_path.expanduser()
        path.mkdir(parents=True, exist_ok=True)
        return QdrantClient(path=str(path))
    return QdrantClient(location=":memory:")


__all__ = ["make_client"]
