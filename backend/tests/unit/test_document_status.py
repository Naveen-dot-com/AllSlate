from backend.app.services.document_status import summarize_document_status


def test_document_status_rollup_for_clean_document():
    elements = [{"confidence": "confident"}, {"confidence": "confident"}]
    assert summarize_document_status(elements) == ("stored", None, False)


def test_document_status_rollup_for_partial_document_below_threshold():
    elements = [
        {"confidence": "confident"},
        {"confidence": "partial"},
        {"confidence": "confident"},
        {"confidence": "confident"},
    ]
    status, reason, has_low_confidence = summarize_document_status(elements)
    assert status == "stored_partial"
    assert reason == "partial content detected"
    assert has_low_confidence is True


def test_document_status_rollup_for_failed_document_above_threshold():
    elements = [
        {"confidence": "partial"},
        {"confidence": "partial"},
        {"confidence": "uncertain"},
        {"confidence": "uncertain"},
    ]
    status, reason, has_low_confidence = summarize_document_status(elements)
    assert status == "failed"
    assert reason == "too much content was low confidence or unreadable"
    assert has_low_confidence is True


def test_document_status_rollup_counts_missing_confidence_as_low_confidence():
    elements = [
        {"confidence": "confident"},
        {"confidence": None},
        {"confidence": "confident"},
        {"confidence": "confident"},
    ]
    status, reason, has_low_confidence = summarize_document_status(elements)
    assert status == "stored_partial"
    assert reason == "partial content detected"
    assert has_low_confidence is True
