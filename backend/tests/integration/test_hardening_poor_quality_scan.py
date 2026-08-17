from backend.app.pipeline.confidence import bucket_confidence


def test_poor_quality_scan_is_not_marked_confident():
    score = bucket_confidence(0.56)
    assert score in {"partial", "uncertain"}
