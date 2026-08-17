from __future__ import annotations

from backend.app.models.document import ProcessedElement
from backend.app.rag.citations import resolve_citation_confidence
from backend.app.rag.retriever import RetrievedChunk


def test_citation_confidence_resolves_via_element_id():
    element = ProcessedElement(
        element_id="el-1",
        element_type="table",
        confidence="partial",
        confidence_reason="irregular table structure (partial)",
    )
    chunk = RetrievedChunk(
        chunk_id="chunk-1",
        document_id="doc-1",
        project_id="proj-1",
        page_content="table content",
        metadata={"element_id": "el-1"},
    )

    result = resolve_citation_confidence(chunk, {"el-1": element})

    assert result == ("partial", "irregular table structure (partial)")


def test_citation_confidence_returns_none_when_no_element_id():
    chunk = RetrievedChunk(
        chunk_id="chunk-2",
        document_id="doc-1",
        project_id="proj-1",
        page_content="text",
    )

    assert resolve_citation_confidence(chunk, {}) is None
