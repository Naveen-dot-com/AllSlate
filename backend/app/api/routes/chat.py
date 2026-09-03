from __future__ import annotations

import json
from typing import Any, AsyncIterator, Dict, List

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.app.models.message import MessageStatus
from backend.app.rag.generation import AnswerGenerator
from backend.app.rag.graph import RagChatGraph
from backend.app.rag.retriever import RetrievedChunk
from backend.app.services.conversation_service import ConversationService
from backend.app.services.document_store import document_store
from backend.app.services.message_service import MessageService
from backend.app.api.routes.conversation_settings import get_settings_service

router = APIRouter(prefix="/api/v1/projects", tags=["chat"])

_conversations = ConversationService()
_messages = MessageService()
def _local_answer(prompt: str) -> str:
    """Predictable local fallback until a production LLM provider is configured."""
    source = prompt.split("Sources:\n", maxsplit=1)[-1].split("\n\nQuestion:", maxsplit=1)[0]
    return f"Based on your processed documents:\n\n{source}"


_graph = RagChatGraph(generator=AnswerGenerator(llm_call=_local_answer))


class CreateConversationRequest(BaseModel):
    title: str | None = None


class AskRequest(BaseModel):
    question: str = Field(min_length=1)


def _get_owned_conversation(project_id: str, conversation_id: str):
    try:
        return _conversations.get_owned(project_id, conversation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="conversation not found") from exc


def _project_candidates(project_id: str, question: str) -> List[RetrievedChunk]:
    question_terms = set(question.lower().split())
    candidates: List[RetrievedChunk] = []
    for document in document_store.list(project_id):
        for element in document.elements:
            content = (element.raw_text or "").strip()
            if not content:
                continue
            content_terms = set(content.lower().split())
            overlap = len(question_terms & content_terms)
            candidates.append(
                RetrievedChunk(
                    chunk_id=element.element_id,
                    document_id=document.document_id,
                    project_id=project_id,
                    page_content=content,
                    element_type=element.element_type,
                    page_number=element.page_number,
                    score=0.9 if overlap else 0.3,
                    metadata={"element_id": element.element_id},
                )
            )
    return candidates


@router.post("/{project_id}/conversations", status_code=201)
async def create_conversation(project_id: str, body: CreateConversationRequest) -> Dict[str, Any]:
    conversation = _conversations.create(project_id, title=body.title)
    return {
        "id": conversation.id,
        "project_id": conversation.project_id,
        "title": conversation.title,
        "created_at": conversation.created_at,
    }


@router.get("/{project_id}/conversations/{conversation_id}/messages")
async def list_messages(project_id: str, conversation_id: str) -> List[Dict[str, Any]]:
    _get_owned_conversation(project_id, conversation_id)
    history = _messages.history(conversation_id)
    return [
        {
            "id": m.id,
            "sequence_number": m.sequence_number,
            "role": m.role.value,
            "content": m.content,
            "status": m.status.value,
            "failure_reason": m.failure_reason,
            "is_grounded": m.is_grounded,
            "created_at": m.created_at,
            "effective_settings_snapshot": m.effective_settings_snapshot,
            "citations": [
                {
                    "document_id": c.document_id,
                    "page_number": c.page_number,
                    "asset_reference_url": c.asset_reference_url,
                }
                for c in m.citations
            ],
        }
        for m in history
    ]


@router.post("/{project_id}/conversations/{conversation_id}/ask")
async def ask(project_id: str, conversation_id: str, body: AskRequest) -> StreamingResponse:
    _get_owned_conversation(project_id, conversation_id)
    if not body.question.strip():
        raise HTTPException(status_code=422, detail="question must not be empty")

    _messages.append_user_message(conversation_id, body.question)
    assistant_message = _messages.append_assistant_message(conversation_id)

    # Settings are resolved exactly once, at submission time, and captured as a
    # detached snapshot: a later mid-flight settings change can never affect
    # this in-progress answer (FR-013), and the snapshot is preserved even if
    # the conversation's live settings later change (FR-014).
    settings_snapshot = get_settings_service().snapshot(conversation_id)

    async def event_stream() -> AsyncIterator[str]:
        candidates = _project_candidates(project_id, body.question)

        def on_phase(phase: str) -> None:
            pass  # phase events are emitted explicitly below to keep ordering deterministic

        yield _sse_event("phase", {"phase": "retrieving"})
        yield _sse_event("phase", {"phase": "generating"})

        result = _graph.ask(
            project_id, body.question, candidates, settings=settings_snapshot, on_phase=on_phase
        )

        if result.status == MessageStatus.FAILED:
            assistant_message.status = MessageStatus.FAILED
            assistant_message.failure_reason = result.failure_reason
            yield _sse_event(
                "failed",
                {"message_id": assistant_message.id, "failure_reason": result.failure_reason},
            )
            return

        assistant_message.status = MessageStatus.COMPLETE
        assistant_message.content = result.content
        assistant_message.is_grounded = result.is_grounded
        assistant_message.citations = result.citations
        assistant_message.effective_settings_snapshot = {
            "web_search_enabled": settings_snapshot.web_search_enabled,
            "creativity_level": settings_snapshot.creativity_level,
            "retrieval_top_k": settings_snapshot.retrieval_top_k,
            "included_document_types": settings_snapshot.included_document_types,
        }

        yield _sse_event(
            "complete",
            {
                "message_id": assistant_message.id,
                "content": result.content,
                "is_grounded": result.is_grounded,
                "citations": [
                    {
                        "document_id": c.document_id,
                        "page_number": c.page_number,
                        "asset_reference_url": c.asset_reference_url,
                    }
                    for c in result.citations
                ],
            },
        )

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _sse_event(event: str, data: Dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"
