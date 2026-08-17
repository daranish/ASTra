
from __future__ import annotations

from typing import Protocol

from astra.config import Settings
from astra.errors import LLMError
from astra.llm.deepseek import DeepSeekClient
from astra.llm.gemma import GemmaClient


class LLMClient(Protocol):

    async def chat(
        self,
        *,
        system: str,
        user: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str: ...


def make_llm_client(settings: Settings) -> LLMClient:
    provider = settings.llm_provider.lower()
    if provider == "deepseek":
        if not settings.deepseek_api_key:
            raise LLMError("DEEPSEEK_API_KEY is required when LLM_PROVIDER=deepseek")
        return DeepSeekClient(settings)
    if provider == "gemma":
        if not settings.google_api_key:
            raise LLMError("GOOGLE_API_KEY is required when LLM_PROVIDER=gemma")
        return GemmaClient(settings)
    raise LLMError(
        f"Unknown LLM_PROVIDER={settings.llm_provider!r}. Expected 'deepseek' or 'gemma'."
    )


__all__ = ["LLMClient", "make_llm_client"]
