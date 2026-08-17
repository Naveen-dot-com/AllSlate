from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


class MessageStatus(str, Enum):
    RETRIEVING = "retrieving"
    GENERATING = "generating"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class MessageCitation:
    chunk_id: str
    document_id: str
    asset_reference_id: Optional[str] = None
    page_number: Optional[int] = None
    asset_reference_url: Optional[str] = None


@dataclass
class Message:
    id: str
    conversation_id: str
    sequence_number: int
    role: MessageRole
    content: Optional[str] = None
    status: MessageStatus = MessageStatus.COMPLETE
    failure_reason: Optional[str] = None
    is_grounded: bool = True
    citations: List[MessageCitation] = field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
