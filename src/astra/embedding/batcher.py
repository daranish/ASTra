
from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from astra.config import Settings
from astra.embedding.gemini import GeminiEmbedder
from astra.errors import EmbeddingError
from astra.logging import get_logger

log = get_logger(__name__)


_RETRY_EXCEPTIONS: tuple[type[BaseException], ...] = (
    asyncio.TimeoutError,
    ConnectionError,
    OSError,
)


async def embed_documents_with_retry(
    embedder: GeminiEmbedder,
    texts: list[str],
    settings: Settings,
) -> list[list[float]]:

    try:
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(6),
            wait=wait_exponential(multiplier=1, min=1, max=60),
            retry=retry_if_exception_type(_RETRY_EXCEPTIONS),
            reraise=True,
        ):
            with attempt:
                return await embedder.embed_documents(texts)
    except Exception as exc:
        log.error("embedding_failed", error=str(exc), n_texts=len(texts))
        raise EmbeddingError(f"Failed to embed {len(texts)} documents: {exc}") from exc
    msg = "embedding loop exited unexpectedly"
    raise EmbeddingError(msg)


async def embed_query_with_retry(
    embedder: GeminiEmbedder, text: str, settings: Settings
) -> list[float]:

    try:
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(4),
            wait=wait_exponential(multiplier=1, min=1, max=30),
            retry=retry_if_exception_type(_RETRY_EXCEPTIONS),
            reraise=True,
        ):
            with attempt:
                return await embedder.embed_query(text)
    except Exception as exc:
        log.error("query_embedding_failed", error=str(exc))
        raise EmbeddingError(f"Failed to embed query: {exc}") from exc
    msg = "query embedding loop exited unexpectedly"
    raise EmbeddingError(msg)


async def run_with_backpressure(
    items: list,
    worker: Callable[[list], Awaitable[list]],
    *,
    batch_size: int,
    concurrency: int,
) -> list:

    sem = asyncio.Semaphore(concurrency)
    batches = [items[i : i + batch_size] for i in range(0, len(items), batch_size)]

    async def run(batch):
        async with sem:
            return await worker(batch)

    return await asyncio.gather(*(run(b) for b in batches))


__all__ = [
    "embed_documents_with_retry",
    "embed_query_with_retry",
    "run_with_backpressure",
]
