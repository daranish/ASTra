
from __future__ import annotations

import openai

from astra.config import Settings
from astra.errors import LLMError
from astra.logging import get_logger

log = get_logger(__name__)


class DeepSeekClient:

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = openai.AsyncOpenAI(
            api_key=settings.deepseek_api_key,
            base_url=settings.llm_base_url,
        )

    async def chat(
        self,
        *,
        system: str,
        user: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        try:
            response = await self._client.chat.completions.create(
                model=self._settings.llm_model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=temperature
                if temperature is not None
                else self._settings.llm_temperature,
                max_tokens=max_tokens if max_tokens is not None else self._settings.llm_max_tokens,
                timeout=self._settings.llm_timeout_sec,
            )
        except openai.APITimeoutError as exc:
            log.error("deepseek_timeout", error=str(exc), timeout=self._settings.llm_timeout_sec)
            raise LLMError(f"DeepSeek timed out after {self._settings.llm_timeout_sec}s") from exc
        except openai.OpenAIError as exc:
            log.error("deepseek_error", error=str(exc))
            raise LLMError(f"DeepSeek call failed: {exc}") from exc
        except Exception as exc:
            log.error("deepseek_unexpected", error=str(exc))
            raise LLMError(f"DeepSeek unexpected error: {exc}") from exc

        if not response.choices:
            raise LLMError("DeepSeek returned no choices")
        content = response.choices[0].message.content
        return content or ""


__all__ = ["DeepSeekClient"]
