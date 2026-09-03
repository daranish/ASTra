from __future__ import annotations

from collections.abc import AsyncIterator
import openai

from astra.config import Settings
from astra.errors import LLMError
from astra.logging import get_logger

log = get_logger(__name__)


class OpenRouterClient:

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = openai.AsyncOpenAI(
            api_key=settings.openrouter_api_key,
            base_url=settings.openrouter_base_url,
            default_headers={
                "HTTP-Referer": "https://github.com/astra",
                "X-Title": "ASTra Code Analyst",
            },
        )

    async def chat(
        self,
        *,
        system: str,
        user: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> str:
        models = [
            self._settings.openrouter_primary_model,
            self._settings.openrouter_fallback_1_model,
            self._settings.openrouter_fallback_2_model,
            self._settings.openrouter_fallback_3_model,           
        ]
        last_error: Exception | None = None

        for idx, model_name in enumerate(models):
            is_fallback = idx > 0
            log_event = "openrouter_fallback_attempt" if is_fallback else "openrouter_chat_attempt"
            log.info(log_event, model=model_name, is_fallback=is_fallback)

            try:
                response = await self._client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    temperature=temperature if temperature is not None else self._settings.llm_temperature,
                    max_tokens=max_tokens if max_tokens is not None else self._settings.llm_max_tokens,
                    timeout=self._settings.llm_timeout_sec,
                )
                if response.choices and response.choices[0].message.content:
                    return response.choices[0].message.content
            except Exception as exc:
                log.warning(
                    "openrouter_model_failed",
                    model=model_name,
                    error=str(exc),
                    will_fallback=(idx < len(models) - 1),
                )
                last_error = exc

        raise LLMError(f"OpenRouter failed for primary ({models[0]}) and fallback 1 ({models[1]}) and fallback 2 ({models[2]}) and fallback 3 ({models[3]}): {last_error}") from last_error

    async def chat_stream(
        self,
        *,
        system: str,
        user: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]:
        models = [
            self._settings.openrouter_primary_model,
            self._settings.openrouter_fallback_1_model,
            self._settings.openrouter_fallback_2_model,
            self._settings.openrouter_fallback_3_model,
        ]
        last_error: Exception | None = None

        for idx, model_name in enumerate(models):
            is_fallback = idx > 0
            log_event = "openrouter_stream_fallback_attempt" if is_fallback else "openrouter_stream_attempt"
            log.info(log_event, model=model_name, is_fallback=is_fallback)

            started = False

            try:
                response = await self._client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    temperature=temperature if temperature is not None else self._settings.llm_temperature,
                    max_tokens=max_tokens if max_tokens is not None else self._settings.llm_max_tokens,
                    timeout=self._settings.llm_timeout_sec,
                    stream=True,
                )
                async for chunk in response:
                    if chunk.choices and chunk.choices[0].delta.content:
                        started = True
                        yield chunk.choices[0].delta.content
                return  # Stream completed successfully
            except Exception as exc:
                log.warning(
                    "openrouter_stream_model_failed",
                    model=model_name,
                    error=str(exc),
                    will_fallback=(idx < len(models) - 1),
                )
                last_error = exc
                if started:
                    raise LLMError(
                        f"OpenRouter streaming failed after "
                        f"response started from model {model_name}: {exc}"
                    ) from exc
                continue

        raise LLMError(f"OpenRouter streaming failed for primary ({models[0]}) and fallback 1 ({models[1]}) and fallback 2 ({models[2]}) and fallback 3 ({models[3]}): {last_error}")


__all__ = ["OpenRouterClient"]