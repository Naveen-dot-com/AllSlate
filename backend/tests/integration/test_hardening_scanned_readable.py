from backend.app.pipeline.confidence import bucket_confidence


def test_scanned_readable_document_is_confident():
    confidence = bucket_confidence(0.9)
    assert confidence == "confident"
