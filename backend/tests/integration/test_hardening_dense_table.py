from backend.app.pipeline.confidence import bucket_table_regularity


def test_dense_table_document_is_tagged_for_review():
    score = bucket_table_regularity(0.72)
    assert score in {"partial", "uncertain"}
