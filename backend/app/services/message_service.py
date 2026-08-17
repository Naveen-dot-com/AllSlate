from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List
from uuid import uuid4

from backend.app.models.message import Message, MessageRole, MessageStatus


class MessageService:
    """Persists messages with strictly increasing per-thread sequence numbers.

    A monotonic, thread-scoped counter (assigned atomically in production via
    a DB sequence or serializable insert) guarantees concurrent `ask` calls in
    the same thread are never lost, duplicated, or misordered (FR-018).
    """

    def __init__(self) -> None:
        self._messages: Dict[str, List[Message]] = {}
        self._next_sequence: Dict[str, int] = {}

    def _next_sequence_number(self, conversation_id: str) -> int:
        current = self._next_sequence.get(conversation_id, 0) + 1
        self._next_sequence[conversation_id] = current
        return current

    def append_user_message(self, conversation_id: str, content: str) -> Message:
        if not content or not content.strip():
            raise ValueError("question text must not be empty")
        message = Message(
            id=str(uuid4()),
            conversation_id=conversation_id,
            sequence_number=self._next_sequence_number(conversation_id),
            role=MessageRole.USER,
            content=content,
            status=MessageStatus.COMPLETE,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._messages.setdefault(conversation_id, []).append(message)
        return message

    def append_assistant_message(self, conversation_id: str) -> Message:
        message = Message(
            id=str(uuid4()),
            conversation_id=conversation_id,
            sequence_number=self._next_sequence_number(conversation_id),
            role=MessageRole.ASSISTANT,
            content=None,
            status=MessageStatus.RETRIEVING,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._messages.setdefault(conversation_id, []).append(message)
        return message

    def history(self, conversation_id: str) -> List[Message]:
        return sorted(
            self._messages.get(conversation_id, []),
            key=lambda m: m.sequence_number,
        )
