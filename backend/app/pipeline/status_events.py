from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from backend.app.models.document import ProcessingStatus


@dataclass
class StatusEvent:
    document_id: str
    stage: ProcessingStatus
    occurred_at: str
    reason: Optional[str] = None


class StatusEventPublisher:
    def __init__(self) -> None:
        self.events: list[StatusEvent] = []

    def emit(self, document_id: str, stage: ProcessingStatus, reason: Optional[str] = None) -> StatusEvent:
        event = StatusEvent(
            document_id=document_id,
            stage=stage,
            occurred_at=datetime.now(timezone.utc).isoformat(),
            reason=reason,
        )
        self.events.append(event)
        return event
