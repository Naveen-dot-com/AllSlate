from __future__ import annotations

from backend.app.models.document import Document, ProcessedElement
from backend.app.pipeline.graph import resolve_document_outcome
from backend.app.services.document_status import document_detail_fields


def test_fully_confident_document_has_no_partial_indicators():
    elements = [
        ProcessedElement(element_id="e1", element_type="text", confidence="confident"),
        ProcessedElement(element_id="e2", element_type="text", confidence="confident"),
        ProcessedElement(element_id="e3", element_type="table", confidence="confident"),
    ]
    document = Document(
        document_id="doc-clean",
        filename="clean.pdf",
        file_type="pdf",
        elements=elements,
        element_count=len(elements),
    )

    outcome = resolve_document_outcome(document.document_id, [{"confidence": e.confidence} for e in elements])
    document.status = outcome.current_status
    document.failure_category = outcome.failure_category

    detail = document_detail_fields(document)

    assert detail["status"] == "stored"
    assert detail["failure_category"] is None
    assert detail["has_low_confidence_content"] is False
    assert all(e.confidence_reason is None for e in elements)
