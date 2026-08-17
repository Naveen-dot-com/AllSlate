from __future__ import annotations

from backend.app.models.document import Document, ProcessedElement, ProcessingStatus
from backend.app.pipeline.graph import resolve_document_outcome
from backend.app.services.document_status import document_detail_fields


def _document_with_elements(elements: list[ProcessedElement]) -> Document:
    return Document(
        document_id="doc-mixed",
        filename="mixed.pdf",
        file_type="pdf",
        elements=elements,
        element_count=len(elements),
    )


def test_mixed_confidence_document_shows_correct_markers_and_rollup():
    elements = [
        ProcessedElement(element_id="e1", element_type="text", confidence="confident"),
        ProcessedElement(
            element_id="e2",
            element_type="table",
            confidence="partial",
            confidence_reason="irregular table structure (partial)",
        ),
        ProcessedElement(element_id="e3", element_type="text", confidence="confident"),
        ProcessedElement(element_id="e4", element_type="text", confidence="confident"),
    ]
    document = _document_with_elements(elements)

    outcome = resolve_document_outcome(document.document_id, [{"confidence": e.confidence} for e in elements])
    document.status = outcome.current_status
    document.failure_category = outcome.failure_category

    detail = document_detail_fields(document)

    assert detail["status"] == "stored_partial"
    assert detail["has_low_confidence_content"] is True
    # Only the table element should carry a partial marker + reason.
    assert elements[1].confidence == "partial"
    assert elements[1].confidence_reason is not None
    assert all(e.confidence == "confident" for e in (elements[0], elements[2], elements[3]))
