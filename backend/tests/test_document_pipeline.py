from backend.app.models.document import Document, ProcessedElement, ProcessingStatus
from backend.app.pipeline.graph import PipelineGraph, PipelineState, advance_status
from backend.app.services.document_upload import DocumentUploadService


def test_pipeline_status_advances_in_order():
    graph = PipelineGraph()
    state = PipelineState(document_id="doc-123", current_status=ProcessingStatus.UPLOADED)

    next_state = graph.advance(state)

    assert next_state.current_status == ProcessingStatus.QUEUED
    assert next_state.document_id == "doc-123"


def test_document_upload_rejects_unsupported_types():
    service = DocumentUploadService()

    try:
        service.validate_upload("bad.xyz")
        raise AssertionError("Expected unsupported file type validation failure")
    except ValueError as exc:
        assert "Unsupported" in str(exc)


def test_processed_element_tracks_source_metadata():
    element = ProcessedElement(
        element_id="el-1",
        element_type="table",
        page_number=2,
        raw_text="Monthly revenue",
        asset_reference="storage/projects/p1/table-1.png",
    )

    assert element.element_type == "table"
    assert element.page_number == 2
    assert element.asset_reference.endswith("table-1.png")


def test_advance_status_handles_failure_reason():
    state = PipelineState(document_id="doc-456", current_status=ProcessingStatus.PARTITIONING)
    next_state = advance_status(state, ProcessingStatus.FAILED, reason="OCR failed")

    assert next_state.current_status == ProcessingStatus.FAILED
    assert next_state.failure_reason == "OCR failed"
