
from __future__ import annotations

import os

import pytest

os.environ.setdefault("DEEPSEEK_API_KEY", "test-deepseek-key")
os.environ.setdefault("GOOGLE_API_KEY", "test-google-key")


@pytest.fixture
def settings():
    from astra.config import get_settings

    get_settings.cache_clear()  # type: ignore[attr-defined]
    return get_settings()
