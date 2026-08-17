from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.api.routes.conversation_settings import router as settings_router


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(settings_router)
    return TestClient(app)


def test_get_settings_creates_defaults_on_first_read() -> None:
    client = _client()

    response = client.get("/api/v1/projects/project-1/conversations/conv-1/settings")

    assert response.status_code == 200
    body = response.json()
    assert body["web_search_enabled"] is False
    assert body["creativity_level"] == "balanced"
    assert body["retrieval_top_k"] == 8
    assert body["included_document_types"] == ["all"]


def test_patch_settings_persists_partial_update() -> None:
    client = _client()

    response = client.patch(
        "/api/v1/projects/project-1/conversations/conv-1/settings",
        json={"web_search_enabled": True, "creativity_level": "creative"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["web_search_enabled"] is True
    assert body["creativity_level"] == "creative"
    assert body["retrieval_top_k"] == 8


def test_patch_settings_rejects_empty_document_types_with_422() -> None:
    client = _client()

    response = client.patch(
        "/api/v1/projects/project-1/conversations/conv-1/settings",
        json={"included_document_types": []},
    )

    assert response.status_code == 422


def test_patch_settings_rejects_out_of_range_top_k_with_422() -> None:
    client = _client()

    response = client.patch(
        "/api/v1/projects/project-1/conversations/conv-1/settings",
        json={"retrieval_top_k": 100},
    )

    assert response.status_code == 422


def test_patch_settings_rejects_invalid_creativity_level_with_422() -> None:
    client = _client()

    response = client.patch(
        "/api/v1/projects/project-1/conversations/conv-1/settings",
        json={"creativity_level": "unhinged"},
    )

    assert response.status_code == 422
