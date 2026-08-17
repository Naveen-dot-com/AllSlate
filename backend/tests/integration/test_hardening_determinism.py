from __future__ import annotations

from backend.app.pipeline.graph import resolve_document_outcome


def test_reprocessing_same_fixture_three_times_is_deterministic():
    elements = [
        {"confidence": "confident"},
        {"confidence": "partial"},
        {"confidence": "confident"},
        {"confidence": "confident"},
    ]

    outcomes = [resolve_document_outcome("doc-repro", elements) for _ in range(3)]

    statuses = {outcome.current_status for outcome in outcomes}
    reasons = {outcome.failure_reason for outcome in outcomes}
    categories = {outcome.failure_category for outcome in outcomes}

    assert len(statuses) == 1
    assert len(reasons) == 1
    assert len(categories) == 1
