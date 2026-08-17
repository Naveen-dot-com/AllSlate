from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from backend.app.models.document import ProcessingStatus


@dataclass
class PipelineState:
    document_id: str
    current_status: ProcessingStatus
    failure_reason: Optional[str] = None


class PipelineGraph:
    status_order = [
        ProcessingStatus.UPLOADED,
        ProcessingStatus.QUEUED,
        ProcessingStatus.PARTITIONING,
        ProcessingStatus.CHUNKING,
        ProcessingStatus.SUMMARIZING,
        ProcessingStatus.VECTORIZING,
        ProcessingStatus.STORED,
    ]

    def advance(self, state: PipelineState) -> PipelineState:
        idx = self.status_order.index(state.current_status)
        next_status = self.status_order[min(idx + 1, len(self.status_order) - 1)]
        return PipelineState(
            document_id=state.document_id,
            current_status=next_status,
            failure_reason=None,
        )


def advance_status(state: PipelineState, new_status: ProcessingStatus, reason: Optional[str] = None) -> PipelineState:
    return PipelineState(
        document_id=state.document_id,
        current_status=new_status,
        failure_reason=reason if new_status == ProcessingStatus.FAILED else None,
    )
