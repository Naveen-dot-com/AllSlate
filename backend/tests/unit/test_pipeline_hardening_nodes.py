from backend.app.models.document import ProcessingStatus
from backend.app.pipeline.graph import (
    PipelineState,
    resolve_document_outcome,
    route_node_failure,
)
from backend.app.pipeline.nodes.ocr import OCRProcessor
from backend.app.pipeline.nodes.partition import PartitionProcessor
from backend.app.pipeline.status_events import StatusEventPublisher


def test_ocr_processor_attaches_confidence_from_score():
    result = OCRProcessor().process("scan.pdf", "some text", confidence_score=0.9)
    assert result.confidence == "confident"
    assert result.confidence_reason is None


def test_ocr_processor_flags_low_confidence_scan():
    result = OCRProcessor().process("scan.pdf", "some text", confidence_score=0.4)
    assert result.confidence == "uncertain"
    assert result.confidence_reason is not None


def test_ocr_processor_marks_illegible_scan_uncertain():
    result = OCRProcessor().process("scan.pdf", "")
    assert result.confidence == "uncertain"
    assert result.confidence_reason == "no readable text recovered from scan"


def test_partition_processor_flags_irregular_table():
    result = PartitionProcessor().process(
        "row | row", "doc.pdf", element_type="table", table_regularity_score=0.65
    )
    element = result.elements[0]
    assert element.confidence in {"partial", "uncertain"}
    assert element.confidence_reason is not None


def test_partition_processor_flags_unsupported_language_without_failing():
    result = PartitionProcessor().process(
        "contenu", "doc.pdf", element_type="text", language="de"
    )
    element = result.elements[0]
    assert element.confidence_reason == "unsupported_language_segment"
    assert element.raw_text == "contenu"


def test_route_node_failure_maps_specific_category():
    state = PipelineState(document_id="doc-1", current_status=ProcessingStatus.PARTITIONING)
    failed_state = route_node_failure(state, "malformed_table", "table 2")

    assert failed_state.current_status == ProcessingStatus.FAILED
    assert failed_state.failure_category == "malformed_table"
    assert "table" in failed_state.failure_reason


def test_resolve_document_outcome_stored_partial_emits_event():
    elements = [
        {"confidence": "confident"},
        {"confidence": "confident"},
        {"confidence": "confident"},
        {"confidence": "partial"},
    ]
    outcome = resolve_document_outcome("doc-2", elements)
    assert outcome.current_status == ProcessingStatus.STORED_PARTIAL

    publisher = StatusEventPublisher()
    event = publisher.emit_outcome(outcome)
    assert event.stage == ProcessingStatus.STORED_PARTIAL
    assert publisher.events[-1] is event


def test_resolve_document_outcome_failed_has_specific_category():
    elements = [{"confidence": "uncertain"}, {"confidence": "uncertain"}]
    outcome = resolve_document_outcome("doc-3", elements)
    assert outcome.current_status == ProcessingStatus.FAILED
    assert outcome.failure_category is not None
