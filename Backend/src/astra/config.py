
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Secrets (required) ---
    openrouter_api_key: str = Field(..., description="OpenRouter API key")


    # --- Qdrant (optional; defaults to in-memory) ---
    qdrant_url: str | None = Field(
        default=None, description="Qdrant server URL. None → in-process :memory:"
    )
    qdrant_api_key: str | None = Field(default=None, description="Qdrant API key (cloud)")
    qdrant_collection: str = Field(default="astra_code_chunks", description="Collection name")
    qdrant_persist_path: Path | None = Field(
        default=None,
        description=(
            "On-disk path for the local Qdrant store. If set, takes precedence over "
            "`:memory:` so data survives restarts. Ignored when `qdrant_url` is set."
        ),
    )

    # --- Embedding ---
    embedding_model: str = Field(default="nvidia/nemotron-3-embed-1b:free", description="OpenRouter embedding model slug")
    embedding_dims: int = Field(
        default=1024, description="Embedding dimensionality (1024 for nemotron-3-embed-1b; MUST match Qdrant collection index)"
    )
    embedding_batch_size: int = Field(default=128, ge=1, le=1000, description="Texts per batch")
    embedding_concurrency: int = Field(default=4, ge=1, le=16, description="Max concurrent batches")

    llm_provider: Literal["primary", "secondary", "auto_fallback"] = Field(
        default="auto_fallback",
        description="LLM mode: 'primary', 'secondary', or 'auto_fallback' (tries primary, falls back to secondary if primary fails)",
    )

    # --- OpenRouter Configuration ---
    openrouter_base_url: str = Field(default="https://openrouter.ai/api/v1", description="OpenRouter base URL")
    openrouter_primary_model: str = Field(
        default="nvidia/nemotron-3-ultra-550b-a55b:free", description="Primary OpenRouter model"
    )
    openrouter_fallback_1_model: str = Field(
        default="cohere/north-mini-code:free", description="1st Fallback OpenRouter model"
    )
    openrouter_fallback_2_model: str = Field(
        default="z-ai/glm-5.2:free", description="2nd Fallback OpenRouter model"
    )
    openrouter_fallback_3_model: str = Field(
        default="deepseek/deepseek-v4-flash-0731", description="3rd Fallback OpenRouter model"
    )
    llm_max_tokens: int = Field(default=1500, ge=64, le=8000, description="Max output tokens")
    llm_temperature: float = Field(default=0.2, ge=0.0, le=2.0, description="Sampling temperature")
    llm_timeout_sec: float = Field(default=60.0, gt=0, description="Per-call LLM timeout")
    embedding_timeout_sec: float = Field(
        default=120.0, gt=0, description="Per-batch embedding timeout"
    )

    # --- Chunking ---
    max_chunk_tokens: int = Field(default=1500, ge=128, le=8000, description="Soft cap per chunk")
    window_tokens: int = Field(default=800, ge=64, le=4000, description="Sliding-window size")
    window_overlap: int = Field(default=100, ge=0, le=400, description="Sliding-window overlap")

    # --- Ingestion ---
    ingest_timeout_sec: int = Field(default=900, ge=30, description="Total ingestion timeout")
    repo_temp_dir: Path = Field(default=Path("D:/Projects 2026/ASTra/astra_repos"), description="Clone cache dir") #Repo's cloned here
    max_file_size_bytes: int = Field(default=2_000_000, description="Skip files larger than this")

    # --- RAG ---
    retrieval_top_k: int = Field(default=30, ge=1, le=200, description="Top-k chunks from Qdrant")
    retrieval_score_threshold: float = Field(default=0.2, ge=0.0, le=1.0)

    # --- Observability ---
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(default="INFO")
    log_json: bool = Field(default=True, description="Emits JSON logs")

    # --- Security / proxy ---
    # Comma-separated lists. Empty / "*" means "no restriction".
    # In production, set both to concrete values to lock the API down.
    allowed_hosts: list[str] = Field(
        default_factory=lambda: ["*"],
        description="Trusted hosts (TrustedHostMiddleware). Use ['*'] to disable.",  #configure before deploying
    )
    cors_allow_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:3000"],
        description="CORS allow-origins. Empty list disables CORS entirely.",   #configure before deploying
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


__all__ = ["Settings", "get_settings"]
