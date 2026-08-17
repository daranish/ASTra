"""Health endpoints: liveness (always 200) and readiness (checks dependencies)."""

from __future__ import annotations

from fastapi import APIRouter, Request

from astra.api.deps import settings_dep
from astra.api.schemas import HealthResponse
from astra.config import Settings

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def liveness() -> HealthResponse:
    """Always returns 200 — the process is up."""
    return HealthResponse(status="ok", qdrant=True, has_deepseek_key=True, has_google_key=True)


@router.get("/health/ready", response_model=HealthResponse)
async def readiness(request: Request, settings: Settings = None) -> HealthResponse:  # type: ignore[assignment]
    """Returns 200 only if Qdrant responds and required keys are configured."""

    if settings is None:
        settings = settings_dep()

    qdrant_ok = True
    details: dict[str, str] = {}
    try:
        client = request.app.state.qdrant
        client.get_collections()  # cheap call
    except Exception as exc:
        qdrant_ok = False
        details["qdrant_error"] = str(exc)

    return HealthResponse(
        status="ready" if qdrant_ok else "degraded",
        qdrant=qdrant_ok,
        has_deepseek_key=bool(settings.deepseek_api_key),
        has_google_key=bool(settings.google_api_key),
        details=details,
    )
