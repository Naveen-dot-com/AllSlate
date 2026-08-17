from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.api.routes.chat import router as chat_router


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(chat_router)
    return TestClient(app)


def test_create_conversation_returns_201() -> None:
    client = _client()

    response = client.post("/api/v1/projects/project-1/conversations", json={"title": "Thread"})

    assert response.status_code == 201
    body = response.json()
    assert body["project_id"] == "project-1"
    assert body["title"] == "Thread"


def test_ask_rejects_unknown_conversation_with_404() -> None:
    client = _client()

    response = client.post(
        "/api/v1/projects/project-1/conversations/missing/ask",
        json={"question": "hello"},
    )

    assert response.status_code == 404


def test_ask_rejects_empty_question_with_422() -> None:
    client = _client()
    conversation = client.post("/api/v1/projects/project-1/conversations", json={}).json()

    response = client.post(
        f"/api/v1/projects/project-1/conversations/{conversation['id']}/ask",
        json={"question": "   "},
    )

    assert response.status_code == 422


def test_ask_streams_phase_and_complete_events() -> None:
    client = _client()
    conversation = client.post("/api/v1/projects/project-1/conversations", json={}).json()

    with client.stream(
        "POST",
        f"/api/v1/projects/project-1/conversations/{conversation['id']}/ask",
        json={"question": "hello"},
    ) as response:
        assert response.status_code == 200
        body = "".join(response.iter_text())

    assert "event: phase" in body
    assert '"phase": "retrieving"' in body
    assert '"phase": "generating"' in body
    assert "event: complete" in body


def test_messages_endpoint_lists_history_in_order() -> None:
    client = _client()
    conversation = client.post("/api/v1/projects/project-1/conversations", json={}).json()
    conversation_id = conversation["id"]

    with client.stream(
        "POST",
        f"/api/v1/projects/project-1/conversations/{conversation_id}/ask",
        json={"question": "hello"},
    ) as response:
        list(response.iter_text())

    history = client.get(
        f"/api/v1/projects/project-1/conversations/{conversation_id}/messages"
    ).json()

    assert [m["role"] for m in history] == ["user", "assistant"]
    assert [m["sequence_number"] for m in history] == [1, 2]
