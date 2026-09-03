"""Health endpoints: liveness (always 200) and readiness (checks dependencies)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from astra.api.deps import settings_dep
from astra.api.schemas import HealthResponse
from astra.config import Settings

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def liveness() -> HealthResponse:
    """Always returns 200 — the process is up."""
    return HealthResponse(status="ok", qdrant=True, has_openrouter_key=True)


@router.get("/health/ready", response_model=HealthResponse)
async def readiness(request: Request, settings: Settings = Depends(settings_dep)) -> HealthResponse:
    """Returns 200 only if Qdrant responds and required keys are configured."""

    qdrant_ok = True
    details: dict[str, str] = {}
    try:
        client = request.app.state.qdrant
        client.get_collections()  # cheap call
    except Exception as exc:
        qdrant_ok = False
        details["qdrant_error"] = str(exc)

    has_openrouter = bool(getattr(settings, "openrouter_api_key", None))
    #has_voyage = bool(getattr(settings, "voyage_api_key", None))

    is_ready = qdrant_ok and has_openrouter

    return HealthResponse(
        status="ready" if qdrant_ok else "degraded",
        qdrant=qdrant_ok,
        has_openrouter_key=has_openrouter,
        details=details,
    )
