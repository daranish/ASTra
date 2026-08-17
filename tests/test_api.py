
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from astra.api.app import create_app
from astra.config import get_settings


@pytest.fixture
def client():
    get_settings.cache_clear()
    app = create_app()
    # Use the context manager so the lifespan (and app.state init) runs.
    with TestClient(app) as c:
        yield c


def test_liveness(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"


def test_readiness_reports_keys(client):
    r = client.get("/health/ready")
    assert r.status_code == 200
    body = r.json()
    assert body["has_deepseek_key"] is True
    assert body["has_google_key"] is True
    assert "qdrant" in body


def test_ingest_rejects_non_github_url(client):
    r = client.post("/ingest", json={"repo_url": "https://gitlab.com/foo/bar"})
    assert r.status_code == 400
    assert "Invalid GitHub URL" in r.json()["detail"]


def test_ingest_accepts_github_url(client):
    r = client.post("/ingest", json={"repo_url": "https://github.com/pallets/flask"})
    assert r.status_code == 202
    body = r.json()
    assert "job_id" in body
    assert body["repo_url"] == "https://github.com/pallets/flask"
    assert body["status"] == "queued"


def test_ingest_status_not_found(client):
    r = client.get("/ingest/nonexistent-job-id")
    assert r.status_code == 404


def test_ingest_status_returns_job(client):
    r1 = client.post("/ingest", json={"repo_url": "https://github.com/x/y"})
    job_id = r1.json()["job_id"]
    r2 = client.get(f"/ingest/{job_id}")
    assert r2.status_code == 200
    body = r2.json()
    assert body["job_id"] == job_id
    assert body["repo_url"] == "https://github.com/x/y"


def test_query_requires_question(client):
    r = client.post("/query", json={"repo": "https://github.com/x/y", "question": ""})
    assert r.status_code == 422  # pydantic validation


def test_query_missing_fields(client):
    r = client.post("/query", json={"repo": "https://github.com/x/y"})
    assert r.status_code == 422
