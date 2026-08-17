from __future__ import annotations

from backend.app.models.document import ProcessingStatus
from backend.app.pipeline.graph import PipelineState, route_node_failure
from backend.app.pipeline.status_events import StatusEventPublisher


def test_three_hardening_fixtures_produce_distinguishable_failures():
    publisher = StatusEventPublisher()
    scenarios = [
        ("doc-illegible", "illegible_scan", "pages 4-7"),
        ("doc-malformed-table", "malformed_table", "table 2"),
        ("doc-unsupported-language", "unsupported_language", "French"),
    ]

    outcomes = []
    for document_id, category, context in scenarios:
        state = PipelineState(document_id=document_id, current_status=ProcessingStatus.PARTITIONING)
        failed_state = route_node_failure(state, category, context)
        publisher.emit_outcome(failed_state)
        outcomes.append(failed_state)

    categories = {outcome.failure_category for outcome in outcomes}
    reasons = {outcome.failure_reason for outcome in outcomes}

    assert len(categories) == 3
    assert len(reasons) == 3

    for event in publisher.events:
        assert event.failure_category is not None
        assert event.reason is not None
