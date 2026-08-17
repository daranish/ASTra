
from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Literal

JobStatus = Literal["queued", "cloning", "parsing", "embedding", "indexing", "completed", "failed"]


@dataclass
class IngestJob:
    job_id: str
    repo_url: str
    ingestion_id: str
    status: JobStatus = "queued"
    started_at: float = field(default_factory=time.time)
    finished_at: float | None = None
    files_total: int = 0
    files_done: int = 0
    chunks_total: int = 0
    chunks_indexed: int = 0
    error: str | None = None

    def to_dict(self) -> dict:
        return asdict(self)


class JobStore:

    def __init__(self) -> None:
        self._jobs: dict[str, IngestJob] = {}
        self._lock = asyncio.Lock()

    async def create(self, repo_url: str) -> IngestJob:
        async with self._lock:
            job = IngestJob(job_id=str(uuid.uuid4()), repo_url=repo_url)
            self._jobs[job.job_id] = job
            return job

    async def get(self, job_id: str) -> IngestJob | None:
        async with self._lock:
            return self._jobs.get(job_id)

    async def update(self, job_id: str, **fields) -> IngestJob | None:
        async with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return None
            for k, v in fields.items():
                if hasattr(job, k):
                    setattr(job, k, v)
            return job

    async def mark_done(self, job_id: str) -> IngestJob | None:
        return await self.update(job_id, status="completed", finished_at=time.time())

    async def mark_failed(self, job_id: str, error: str) -> IngestJob | None:
        return await self.update(job_id, status="failed", error=error, finished_at=time.time())

    async def count_active(self) -> int:
        active = {"cloning", "parsing", "embedding", "indexing"}
        async with self._lock:
            return sum(1 for j in self._jobs.values() if j.status in active)

    async def all_active_ids(self) -> list[str]:
        async with self._lock:
            return [
                j.job_id
                for j in self._jobs.values()
                if j.status in {"queued", "cloning", "parsing", "embedding", "indexing"}
            ]


async def shutdown_mark_running(store: JobStore) -> None:
    for jid in await store.all_active_ids():
        await store.mark_failed(jid, "server restarted during ingestion; rerun POST /ingest")


__all__ = ["IngestJob", "JobStatus", "JobStore", "shutdown_mark_running"]
