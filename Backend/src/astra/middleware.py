from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from astra.logging import ingestion_id_var, repo_var, request_id_var

MAX_BODY_BYTES = 64 * 1024


class RequestIDMiddleware(BaseHTTPMiddleware):

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        rid = request.headers.get("x-request-id") or str(uuid.uuid4())

        request_id_var.set(rid)

        structlog.contextvars.clear_contextvars()

        structlog.contextvars.bind_contextvars(
            request_id=rid,
            path=request.url.path,
        )

        if request.method not in ("GET", "HEAD", "OPTIONS"):
            cl = request.headers.get("content-length")

            if cl is not None:
                try:
                    if int(cl) > MAX_BODY_BYTES:
                        return Response(
                            content="Request body too large",
                            status_code=413,
                        )
                except ValueError:
                    pass

        try:
            response = await call_next(request)

        finally:
            request_id_var.set(None)
            ingestion_id_var.set(None)
            repo_var.set(None)

            structlog.contextvars.clear_contextvars()

        response.headers["x-request-id"] = rid

        return response


def bind_background_context(
    ingestion_id: str | None = None,
    repo: str | None = None,
) -> None:

    if ingestion_id is not None:
        ingestion_id_var.set(ingestion_id)

    if repo is not None:
        repo_var.set(repo)

    structlog.contextvars.bind_contextvars(
        request_id=request_id_var.get() or "-",
        ingestion_id=ingestion_id_var.get() or "-",
        repo=repo_var.get() or "-",
    )


__all__ = [
    "MAX_BODY_BYTES",
    "RequestIDMiddleware",
    "bind_background_context",
]