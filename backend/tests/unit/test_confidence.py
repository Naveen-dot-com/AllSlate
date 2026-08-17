from backend.app.pipeline.confidence import bucket_confidence, bucket_table_regularity


def test_bucket_confidence_classifies_scores():
    assert bucket_confidence(0.9) == "confident"
    assert bucket_confidence(0.7) == "partial"
    assert bucket_confidence(0.4) == "uncertain"


def test_bucket_table_regularity_classifies_scores():
    assert bucket_table_regularity(0.9) == "confident"
    assert bucket_table_regularity(0.7) == "partial"
    assert bucket_table_regularity(0.4) == "uncertain"
