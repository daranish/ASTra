"""RAG pipeline: embed query → retrieve → build prompt → LLM answer."""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from qdrant_client import QdrantClient

from astra.config import Settings
from astra.embedding.openrouter import OpenRouterEmbedder
from astra.errors import RepoNotIngested
from astra.ingestion.cloner import canonical_repo_key
from astra.llm.factory import LLMClient
from astra.llm.prompts import SYSTEM_PROMPT, build_context_block, build_user_prompt
from astra.logging import get_logger
from astra.rag.citations import hit_to_source
from astra.vectorstore.repository import search

log = get_logger(__name__)


@dataclass(frozen=True)
class Answer:
    answer: str
    sources: list[dict[str, Any]]


class RAGPipeline:

    def __init__(
        self,
        *,
        settings: Settings,
        qdrant: QdrantClient,
        embedder: OpenRouterEmbedder,
        llm: LLMClient,
    ) -> None:
        self._settings = settings
        self._qdrant = qdrant
        self._embedder = embedder
        self._llm = llm

    async def answer(self, repo_url: str, ingestion_id: str, question: str) -> Answer:
        repo = canonical_repo_key(repo_url)
        log.info("rag_query", repo=repo, question_len=len(question))

        # 1. Embed the question (RETRIEVAL_QUERY task type)
        query_vec = await self._embedder.embed_query(question)

        # 2. Retrieve top-k chunks
        hits = search(
            self._qdrant,
            query_vec,
            repo=repo,
            ingestion_id=ingestion_id,
            settings=self._settings,
            query_text=question,
        )
        if not hits:
            return Answer(
                answer="Oops!, It seems I do not have access to any code context for this repository matching your query, so I cannot answer your question. Try asking different question.",
                sources=[]
            )

        # 3. Build prompt
        context = build_context_block(hits)
        user_prompt = build_user_prompt(question, context)

        # 4. Call the configured LLM (DeepSeek or Gemma per LLM_PROVIDER)
        answer_text = await self._llm.chat(system=SYSTEM_PROMPT, user=user_prompt)

        # 5. Format sources
        sources = [hit_to_source(h) for h in hits]

        log.info("rag_answer", repo=repo, n_sources=len(sources), answer_len=len(answer_text))
        return Answer(answer=answer_text, sources=sources)

    async def answer_stream(self, repo_url: str, ingestion_id: str, question: str) -> AsyncIterator[dict[str, Any]]:

        repo = canonical_repo_key(repo_url)
        log.info("rag_stream_query", repo=repo, question_len=len(question))

        # 1. Embed the question
        query_vec = await self._embedder.embed_query(question)

        # 2. Retrieve top-k chunks
        hits = search(
            self._qdrant,
            query_vec,
            repo=repo,
            ingestion_id=ingestion_id,
            settings=self._settings,
            query_text=question,
        )

        if not hits:
            yield {
                "type": "sources",
                "data": [],
            }
            yield {
                "type": "chunk",
                "data": "Oops!, It seems I do not have access to...",
            }
            yield {
                "type": "done",
            }
            return

        # 3. Format sources
        sources = [hit_to_source(h) for h in hits]

        # Send sources first
        yield {
            "type": "sources",
            "data": sources,
        }

        # 4. Build prompt
        context = build_context_block(hits)
        user_prompt = build_user_prompt(question, context)

        # 5. Stream LLM response
        async for chunk in self._llm.chat_stream(
            system=SYSTEM_PROMPT,
            user=user_prompt,
        ):
            yield {
                "type": "chunk",
                "data": chunk,
            }

        # 6. Tell client we're finished
        yield {
            "type": "done",
        }

        log.info(
            "rag_stream_answer",
            repo=repo,
            n_sources=len(sources),
        )


__all__ = ["Answer", "RAGPipeline"]
