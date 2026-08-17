
from __future__ import annotations

import asyncio

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from astra.config import Settings
from astra.errors import LLMError
from astra.logging import get_logger

log = get_logger(__name__)


class GemmaClient:

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = genai.Client(api_key=settings.google_api_key)

    async def chat(
        self,
        *,
        system: str,
        user: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        config = types.GenerateContentConfig(
            system_instruction=system,
            temperature=temperature if temperature is not None else self._settings.llm_temperature,
            max_output_tokens=max_tokens
            if max_tokens is not None
            else self._settings.llm_max_tokens,
        )
        timeout = self._settings.llm_timeout_sec

        try:
            response = await asyncio.wait_for(
                self._client.aio.models.generate_content(
                    model=self._settings.gemma_model,
                    contents=user,
                    config=config,
                ),
                timeout=timeout,
            )
        except TimeoutError as exc:
            log.error(
                "gemma_timeout", error=str(exc), timeout=timeout, model=self._settings.gemma_model
            )
            raise LLMError(f"Gemma timed out after {timeout}s") from exc
        except genai_errors.APIError as exc:
            log.error("gemma_api_error", error=str(exc), model=self._settings.gemma_model)
            raise LLMError(f"Gemma call failed: {exc}") from exc
        except Exception as exc:
            log.error("gemma_unexpected", error=str(exc), model=self._settings.gemma_model)
            raise LLMError(f"Gemma unexpected error: {exc}") from exc

        text = getattr(response, "text", None)
        if text:
            return text

        try:
            parts = response.candidates[0].content.parts
            text = "".join(getattr(p, "text", "") for p in parts if getattr(p, "text", None))
        except (AttributeError, IndexError) as exc:
            raise LLMError("Gemma returned no text content") from exc
        if not text:
            raise LLMError("Gemma returned empty content")
        return text


__all__ = ["GemmaClient"]
