
from __future__ import annotations

import pytest

from astra.config import get_settings
from astra.llm.deepseek import DeepSeekClient
from astra.llm.factory import make_llm_client
from astra.llm.gemma import GemmaClient


def test_factory_returns_deepseek_by_default(monkeypatch):
    get_settings.cache_clear()
    settings = get_settings()
    # Sanity: the default is 'deepseek'.
    assert settings.llm_provider == "deepseek"

    client = make_llm_client(settings)
    assert isinstance(client, DeepSeekClient)


def test_factory_returns_gemma_when_configured(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setenv("LLM_PROVIDER", "gemma")
    get_settings.cache_clear()
    settings = get_settings()
    assert settings.llm_provider == "gemma"

    client = make_llm_client(settings)
    assert isinstance(client, GemmaClient)


def test_factory_rejects_unknown_provider(monkeypatch):
    from pydantic import ValidationError

    monkeypatch.setenv("LLM_PROVIDER", "bogus-model")
    get_settings.cache_clear()
    with pytest.raises(ValidationError) as exc:
        get_settings()
    assert "llm_provider" in str(exc.value).lower() or "deepseek" in str(exc.value).lower()
