from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from astra.logging import get_logger

log = get_logger(__name__)


class AstraError(Exception):

    status_code: int = 500
    code: str = "astra_error"

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class IngestError(AstraError):
    status_code = 500
    code = "ingest_error"


class CloneError(IngestError):
    status_code = 502
    code = "clone_error"


class UnsupportedLanguage(AstraError):
    status_code = 400
    code = "unsupported_language"


class EmbeddingError(AstraError):
    status_code = 502
    code = "embedding_error"


class LLMError(AstraError):
    status_code = 502
    code = "llm_error"


class VectorStoreError(AstraError):
    status_code = 502
    code = "vectorstore_error"


class RepoNotIngested(AstraError):
    status_code = 404
    code = "repo_not_ingested"


class ValidationError(AstraError):
    status_code = 422
    code = "validation_error"


def _to_response(exc: AstraError) -> JSONResponse:
    log.warning("astra_error", code=exc.code, message=exc.message, details=exc.details)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
    )


def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(AstraError)
    async def astra_error_handler(_: Request, exc: AstraError) -> JSONResponse:
        return _to_response(exc)
