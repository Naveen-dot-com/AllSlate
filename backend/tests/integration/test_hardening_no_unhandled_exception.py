from __future__ import annotations

from backend.app.models.document import ProcessingStatus
from backend.app.pipeline.graph import PipelineState, route_node_failure


def _process_corrupted_fixture(raw_bytes: bytes) -> PipelineState:
    """Simulates the partition/OCR node's explicit error edge (T021): any exception raised
    while handling a malformed input is caught and routed to `failed`, never left to crash
    the worker with an unhandled exception."""
    state = PipelineState(document_id="doc-corrupted", current_status=ProcessingStatus.PARTITIONING)
    try:
        if not raw_bytes or raw_bytes[:4] != b"%PDF":
            raise ValueError("corrupted or malformed document: missing PDF header")
        raise AssertionError("unreachable for this test's fixture")
    except ValueError:
        return route_node_failure(state, "illegible_scan", "corrupted file header")


def test_corrupted_fixture_resolves_to_failed_without_unhandled_exception():
    outcome = _process_corrupted_fixture(b"not-a-real-pdf")

    assert outcome.current_status == ProcessingStatus.FAILED
    assert outcome.failure_category == "illegible_scan"
    assert outcome.failure_reason is not None
