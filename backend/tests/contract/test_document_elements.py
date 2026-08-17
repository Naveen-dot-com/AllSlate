from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.api.routes.documents import router as documents_router


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(documents_router)
    return TestClient(app)


def test_document_elements_include_confidence_fields() -> None:
    client = _client()

    response = client.get("/api/v1/projects/project-1/documents/doc-1/elements")

    assert response.status_code == 200
    body = response.json()
    assert len(body) >= 1
    for element in body:
        assert "confidence" in element
        assert element["confidence"] in {"confident", "partial", "uncertain"}
        assert "confidence_reason" in element
