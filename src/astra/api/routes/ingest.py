"""/ingest endpoint — clone, parse, chunk, embed, index. Runs in BackgroundTasks."""

from __future__ import annotations

import os
import shutil
import time
from collections import defaultdict, deque
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request

from astra.api.deps import embedder_dep, job_store_dep, qdrant_dep, settings_dep
from astra.api.schemas import IngestAcceptedResponse, IngestRequest, JobStatusResponse
from astra.chunking.splitter import chunk_file
from astra.config import Settings
from astra.embedding.batcher import embed_documents_with_retry
from astra.embedding.gemini import GeminiEmbedder
from astra.errors import CloneError
from astra.ingestion.cloner import canonical_repo_key, clone_repo, normalize_repo_url
from astra.ingestion.job_store import IngestJob, JobStore
from astra.ingestion.walker import iter_source_files
from astra.logging import get_logger
from astra.middleware import bind_background_context
from astra.vectorstore.repository import delete_repo, upsert_chunks

log = get_logger(__name__)
router = APIRouter(prefix="/ingest", tags=["ingest"])

# Hard cap on simultaneously running ingest jobs in this process. Beyond
# this we 429 to protect memory and external API quotas.
MAX_CONCURRENT_INGESTS = int(os.getenv("ASTRA_MAX_CONCURRENT_INGESTS", "2"))

# Per-IP sliding-window rate limit on /ingest. Each IP gets at most N requests
# in the last WINDOW seconds. In-memory; for multi-replica deploys, swap to
# Redis (`slowapi` is the standard library but is sync; we use a simple deque).
INGEST_RATE_LIMIT = int(os.getenv("ASTRA_INGEST_RATE_LIMIT", "5"))
INGEST_RATE_WINDOW = float(os.getenv("ASTRA_INGEST_RATE_WINDOW_SEC", "60"))
_INGEST_HITS: dict[str, deque[float]] = defaultdict(deque)


def _client_ip(request: Request) -> str:
    """Best-effort client IP. Trusts X-Forwarded-For only if a proxy is configured
    via the `ProxyHeadersMiddleware` chain in production; otherwise returns the
    raw connection peer."""
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def _check_ingest_rate_limit(request: Request) -> None:
    now = time.monotonic()
    ip = _client_ip(request)
    bucket = _INGEST_HITS[ip]
    cutoff = now - INGEST_RATE_WINDOW
    while bucket and bucket[0] < cutoff:
        bucket.popleft()
    if len(bucket) >= INGEST_RATE_LIMIT:
        retry_after = max(1, int(INGEST_RATE_WINDOW - (now - bucket[0])))
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit: max {INGEST_RATE_LIMIT} ingests per {INGEST_RATE_WINDOW:.0f}s per IP",
            headers={"Retry-After": str(retry_after)},
        )
    bucket.append(now)


async def _run_ingest(
    job: IngestJob,
    repo_url: str,
    settings: Settings,
    qdrant,
    embedder: GeminiEmbedder,
    job_store: JobStore,
) -> None:
    """Background ingestion: clone → parse → embed → upsert → done."""
    # Re-bind contextvars: the request middleware's `finally` has already
    # cleared them by the time BackgroundTasks runs.
    bind_background_context(job_id=job.job_id)
    clone_path: Path | None = None
    try:
        # 1. Clone
        await job_store.update(job.job_id, status="cloning")
        try:
            clone_path = await clone_repo(repo_url, settings)
        except CloneError as exc:
            await job_store.mark_failed(job.job_id, f"clone: {exc.message}")
            return

        # 2. Enumerate files
        files = iter_source_files(clone_path, settings)
        repo_key = canonical_repo_key(repo_url)
        bind_background_context(job_id=job.job_id, repo=repo_key)

        # 3. Wipe any previous data for this repo (idempotent re-ingest)
        try:
            delete_repo(qdrant, repo_key, settings)
        except Exception as exc:
            log.warning("delete_repo_failed", error=str(exc), repo=repo_key)

        # 4. Parse + chunk all files
        await job_store.update(job.job_id, status="parsing", files_total=len(files))
        all_chunks: list = []
        for i, path in enumerate(files, start=1):
            try:
                source = path.read_text(encoding="utf-8", errors="replace")
                chunks = chunk_file(path, source, repo=repo_key, settings=settings)
                all_chunks.extend(chunks)
            except Exception as exc:
                log.warning("parse_failed", file=str(path), error=str(exc))
            if i % 25 == 0 or i == len(files):
                await job_store.update(job.job_id, files_done=i, chunks_total=len(all_chunks))

        # 5. Embed + upsert in batches
        await job_store.update(job.job_id, status="embedding", chunks_total=len(all_chunks))
        if all_chunks:
            texts = [c.content for c in all_chunks]
            vectors = await embed_documents_with_retry(embedder, texts, settings)
            await job_store.update(job.job_id, status="indexing")
            upsert_chunks(qdrant, all_chunks, vectors, settings)

        # 6. Done
        await job_store.mark_done(job.job_id)
        log.info("ingest_complete", job_id=job.job_id, repo=repo_key, n_chunks=len(all_chunks))
    except Exception as exc:
        log.exception("ingest_failed", job_id=job.job_id, error=str(exc))
        await job_store.mark_failed(job.job_id, f"unexpected: {exc}")
    finally:
        if clone_path is not None:
            shutil.rmtree(clone_path, ignore_errors=True)


@router.post("", response_model=IngestAcceptedResponse, status_code=202)
async def ingest(
    request: Request,
    payload: IngestRequest,
    background_tasks: BackgroundTasks,
    settings: Settings = Depends(settings_dep),
    job_store: JobStore = Depends(job_store_dep),
    qdrant=Depends(qdrant_dep),
    embedder: GeminiEmbedder = Depends(embedder_dep),
) -> IngestAcceptedResponse:
    """Queue an ingestion job. Returns immediately with a job_id."""
    _check_ingest_rate_limit(request)

    # Validate URL up front (sync, fast).
    try:
        normalize_repo_url(payload.repo_url)
    except CloneError as exc:
        raise HTTPException(status_code=400, detail=exc.message) from exc

    # Reject if too many ingests are already in-flight.
    running = await job_store.count_active()
    if running >= MAX_CONCURRENT_INGESTS:
        raise HTTPException(
            status_code=429,
            detail=f"Server busy: {running} ingestions in progress (max {MAX_CONCURRENT_INGESTS}). Try again later.",
        )

    job = await job_store.create(payload.repo_url)
    background_tasks.add_task(
        _run_ingest,
        job=job,
        repo_url=payload.repo_url,
        settings=settings,
        qdrant=qdrant,
        embedder=embedder,
        job_store=job_store,
    )
    return IngestAcceptedResponse(job_id=job.job_id, repo_url=job.repo_url)


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_status(
    job_id: str,
    job_store: JobStore = Depends(job_store_dep),
) -> JobStatusResponse:
    job = await job_store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"job {job_id} not found")
    return JobStatusResponse(**job.to_dict())


__all__ = ["_run_ingest", "router"]
