from backend.app.models.document import Document, ProcessedElement, ProcessingStatus
from backend.app.pipeline.graph import PipelineGraph, PipelineState, advance_status
from backend.app.services.document_upload import DocumentUploadService


def _make_pdf_with_text(text: str) -> bytes:
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    content = f"BT /F1 12 Tf 50 50 Td ({escaped}) Tj ET"
    stream = content.encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>\n",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>\n",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 200] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\n",
        f"<< /Length {len(stream)} >>\nstream\n".encode("latin-1") + stream + b"\nendstream\n",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\n",
    ]

    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{index} 0 obj\n".encode("latin-1"))
        pdf.extend(obj)
        pdf.extend(b"endobj\n")

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))
    pdf.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("latin-1"))
    return bytes(pdf)


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


def test_document_upload_extracts_pdf_text() -> None:
    service = DocumentUploadService()
    pdf_bytes = _make_pdf_with_text("Quarterly report for AllSlate")

    text = service.extract_text("report.pdf", pdf_bytes)

    assert "Quarterly report for AllSlate" in text


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
