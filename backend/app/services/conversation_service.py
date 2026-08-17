from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List
from uuid import uuid4

from backend.app.models.conversation import Conversation


class ConversationService:
    """In-memory conversation-thread store (Supabase Postgres in production)."""

    def __init__(self) -> None:
        self._conversations: Dict[str, Conversation] = {}

    def create(self, project_id: str, title: str | None = None) -> Conversation:
        if not project_id:
            raise ValueError("project_id is required")
        conversation = Conversation(
            id=str(uuid4()),
            project_id=project_id,
            title=title,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._conversations[conversation.id] = conversation
        return conversation

    def get_owned(self, project_id: str, conversation_id: str) -> Conversation:
        conversation = self._conversations.get(conversation_id)
        if conversation is None or conversation.project_id != project_id:
            raise KeyError("conversation not found for project")
        return conversation

    def list_for_project(self, project_id: str) -> List[Conversation]:
        return [c for c in self._conversations.values() if c.project_id == project_id]
