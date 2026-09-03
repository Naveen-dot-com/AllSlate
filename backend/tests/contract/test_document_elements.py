from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.api.routes.documents import router as documents_router


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(documents_router)
    return TestClient(app)


def _upload_document(client: TestClient) -> str:
    response = client.post(
        "/api/v1/projects/project-1/documents",
        files={"file": ("notes.txt", b"A document with useful notes.", "text/plain")},
    )
    assert response.status_code == 202
    return response.json()["id"]


def test_document_elements_include_confidence_fields() -> None:
    client = _client()

    document_id = _upload_document(client)
    response = client.get(f"/api/v1/projects/project-1/documents/{document_id}/elements")

    assert response.status_code == 200
    body = response.json()
    assert len(body) >= 1
    for element in body:
        assert "confidence" in element
        assert element["confidence"] in {"confident", "partial", "uncertain"}
        assert "confidence_reason" in element
