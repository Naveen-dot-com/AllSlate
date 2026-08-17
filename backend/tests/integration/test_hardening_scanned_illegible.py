from backend.app.services.document_status import summarize_document_status


def test_scanned_illegible_document_rolls_to_partial_or_failed():
    elements = [
        {"confidence": "confident"},
        {"confidence": "partial"},
        {"confidence": "uncertain"},
    ]
    status, _, _ = summarize_document_status(elements)
    assert status in {"stored_partial", "failed"}
