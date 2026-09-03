from __future__ import annotations

import asyncio
import openai

from astra.config import Settings


class OpenRouterEmbedder:

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = openai.AsyncOpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
        )
        self._sem = None  # lazily-initialized asyncio.Semaphore

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return await self._embed(texts)

    async def embed_query(self, text: str) -> list[float]:
        result = await self._embed([text])
        return result[0]

    async def _embed(self, texts: list[str]) -> list[list[float]]:
        if self._sem is None:
            self._sem = asyncio.Semaphore(self._settings.embedding_concurrency)

        batch_size = self._settings.embedding_batch_size
        batches = [texts[i : i + batch_size] for i in range(0, len(texts), batch_size)]
        timeout = self._settings.embedding_timeout_sec

        async def run_one(batch: list[str]) -> list[list[float]]:
            async with self._sem:
                return await asyncio.wait_for(
                    self._call_embed(batch),
                    timeout=timeout,
                )

        results = await asyncio.gather(*(run_one(b) for b in batches), return_exceptions=True)
        out: list[list[float]] = []
        for r in results:
            if isinstance(r, Exception):
                raise r
            out.extend(r)
        return out

    async def _call_embed(self, batch: list[str]) -> list[list[float]]:
        response = await self._client.embeddings.create(
            model=self._settings.embedding_model,
            input=batch,
            encoding_format="float",
        )
        return [e.embedding for e in response.data]


__all__ = ["OpenRouterEmbedder"]