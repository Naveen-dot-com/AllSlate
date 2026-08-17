from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from backend.app.models.document import ProcessingStatus
from backend.app.pipeline.nodes.errors import map_failure_reason


@dataclass
class PipelineState:
    document_id: str
    current_status: ProcessingStatus
    failure_reason: Optional[str] = None
    # FR-014: specific failure category, set only when current_status is FAILED.
    failure_category: Optional[str] = None


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
        failure_category=state.failure_category if new_status == ProcessingStatus.FAILED else None,
    )


def route_node_failure(state: PipelineState, category: str, context: Optional[str] = None) -> PipelineState:
    """T021: explicit error edge from the ocr/partition nodes to the terminal `failed` node.

    Any exception raised by (or confidence-threshold breach detected in) the ocr/partition
    nodes must route here rather than propagate as an unhandled exception, so the worker
    never crashes and the document always reaches a definitive, specific outcome.
    """
    failure_category, failure_reason = map_failure_reason(category, context)
    return PipelineState(
        document_id=state.document_id,
        current_status=ProcessingStatus.FAILED,
        failure_reason=failure_reason,
        failure_category=failure_category,
    )


def resolve_document_outcome(document_id: str, elements: list[dict] | None) -> PipelineState:
    """T022: roll up per-element confidence into the document's final pipeline status."""
    from backend.app.services.document_status import summarize_document_status  # avoid circular import

    status, reason, _ = summarize_document_status(elements)
    if status == "failed":
        failure_category, failure_reason = map_failure_reason("other", reason)
        return PipelineState(
            document_id=document_id,
            current_status=ProcessingStatus.FAILED,
            failure_reason=failure_reason,
            failure_category=failure_category,
        )
    resolved_status = ProcessingStatus.STORED_PARTIAL if status == "stored_partial" else ProcessingStatus.STORED
    return PipelineState(
        document_id=document_id,
        current_status=resolved_status,
        failure_reason=reason if resolved_status == ProcessingStatus.STORED_PARTIAL else None,
    )

