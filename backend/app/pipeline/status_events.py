from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from backend.app.models.document import ProcessingStatus
from backend.app.pipeline.graph import PipelineState


@dataclass
class StatusEvent:
    document_id: str
    stage: ProcessingStatus
    occurred_at: str
    reason: Optional[str] = None
    # T037: persisted alongside `reason` on every hardening-triggered failure.
    failure_category: Optional[str] = None


class StatusEventPublisher:
    def __init__(self) -> None:
        self.events: list[StatusEvent] = []

    def emit(
        self,
        document_id: str,
        stage: ProcessingStatus,
        reason: Optional[str] = None,
        failure_category: Optional[str] = None,
    ) -> StatusEvent:
        event = StatusEvent(
            document_id=document_id,
            stage=stage,
            occurred_at=datetime.now(timezone.utc).isoformat(),
            reason=reason,
            failure_category=failure_category,
        )
        self.events.append(event)
        return event

    def emit_outcome(self, state: PipelineState) -> StatusEvent:
        """T023/T037: record the resolved outcome, including `stored_partial`, and persist
        `failure_reason` together with `failure_category` for every failure."""
        return self.emit(
            state.document_id,
            state.current_status,
            reason=state.failure_reason,
            failure_category=state.failure_category,
        )

