
from __future__ import annotations

from fastapi import Request
from qdrant_client import QdrantClient

from astra.config import Settings, get_settings
from astra.embedding.openrouter import OpenRouterEmbedder
from astra.ingestion.job_store import JobStore
from astra.llm.factory import LLMClient
from astra.rag.pipeline import RAGPipeline
from astra.vectorstore.client import make_client
from astra.vectorstore.schema import ensure_collection


def settings_dep() -> Settings:
    return get_settings()


def qdrant_dep(request: Request) -> QdrantClient:
    return request.app.state.qdrant


def embedder_dep(request: Request) -> OpenRouterEmbedder:
    return request.app.state.embedder


def llm_dep(request: Request) -> LLMClient:
    return request.app.state.llm


def job_store_dep(request: Request) -> JobStore:
    return request.app.state.job_store


def rag_dep(request: Request) -> RAGPipeline:
    return request.app.state.rag


def init_app_state(app) -> None:
    from astra.llm.factory import make_llm_client

    settings = get_settings()
    app.state.settings = settings
    app.state.qdrant = make_client(settings)
    ensure_collection(app.state.qdrant, settings)
    app.state.embedder = OpenRouterEmbedder(settings)
    app.state.llm = make_llm_client(settings)
    app.state.job_store = JobStore()
    app.state.rag = RAGPipeline(
        settings=settings,
        qdrant=app.state.qdrant,
        embedder=app.state.embedder,
        llm=app.state.llm,
    )
