from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.api.routes.documents import router as documents_router


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(documents_router)
    return TestClient(app)


def test_document_detail_includes_hardening_fields() -> None:
    client = _client()

    response = client.get("/api/v1/projects/project-1/documents/doc-1")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {
        "uploaded",
        "queued",
        "partitioning",
        "chunking",
        "summarizing",
        "vectorizing",
        "stored",
        "stored_partial",
        "failed",
    }
    assert "failure_category" in body
    assert "has_low_confidence_content" in body
    assert isinstance(body["has_low_confidence_content"], bool)
