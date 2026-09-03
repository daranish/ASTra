
from __future__ import annotations

import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from astra.api.deps import init_app_state
from astra.api.routes import health, ingest, query
from astra.config import get_settings
from astra.errors import register_exception_handlers
from astra.logging import (
    configure_logging,
    get_logger,
)
from astra.middleware import RequestIDMiddleware

log = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings)
    log.info(
        "app_starting",
        name="astra",
        qdrant=settings.qdrant_url or settings.qdrant_persist_path or "memory",
    )
    init_app_state(app)
    log.info("app_ready")
    try:
        yield
    finally:
        from astra.ingestion.job_store import shutdown_mark_running

        await shutdown_mark_running(app.state.job_store)
        log.info("app_stopping")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="ASTra",
        description="AI-Powered Codebase Analyzer ChatBot",
        version="0.1.0",
        lifespan=lifespan,
    )

    register_exception_handlers(app)

    if settings.allowed_hosts and settings.allowed_hosts != ["*"]:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)

    if settings.cors_allow_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_allow_origins,
            allow_credentials=True,
            allow_methods=["GET", "POST"],
            allow_headers=["Content-Type", "X-Request-ID"],
            max_age=600,
        )

    app.add_middleware(RequestIDMiddleware)

    app.include_router(health.router)
    app.include_router(ingest.router)
    app.include_router(query.router)
    return app


app = create_app()
