
from __future__ import annotations

import asyncio

from google import genai
from google.genai import types

from astra.config import Settings


class GeminiEmbedder:


    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = genai.Client(api_key=settings.google_api_key)
        self._sem = None  # lazily-initialized asyncio.Semaphore

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return await self._embed(texts, task_type="RETRIEVAL_DOCUMENT")

    async def embed_query(self, text: str) -> list[float]:
        result = await self._embed([text], task_type="RETRIEVAL_QUERY")
        return result[0]

    async def _embed(self, texts: list[str], *, task_type: str) -> list[list[float]]:
        if self._sem is None:
            self._sem = asyncio.Semaphore(self._settings.embedding_concurrency)

        config = types.EmbedContentConfig(
            task_type=task_type,
            output_dimensionality=self._settings.embedding_dims,
        )

        batch_size = self._settings.embedding_batch_size
        batches = [texts[i : i + batch_size] for i in range(0, len(texts), batch_size)]
        timeout = self._settings.embedding_timeout_sec

        async def run_one(batch: list[str]) -> list[list[float]]:
            async with self._sem:
                return await asyncio.wait_for(
                    self._call_embed(batch, config),
                    timeout=timeout,
                )

        results = await asyncio.gather(*(run_one(b) for b in batches), return_exceptions=True)
        out: list[list[float]] = []
        for r in results:
            if isinstance(r, Exception):
                raise r
            out.extend(r)
        return out

    async def _call_embed(
        self, batch: list[str], config: types.EmbedContentConfig
    ) -> list[list[float]]:
        response = await self._client.aio.models.embed_content(
            model=self._settings.embedding_model,
            contents=batch,
            config=config,
        )
        return [list(e.values) for e in response.embeddings]


__all__ = ["GeminiEmbedder"]
