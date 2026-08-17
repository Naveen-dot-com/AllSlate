from backend.app.pipeline.nodes.errors import map_failure_reason


def test_failure_mapping_distinguishes_categories():
    categories = {
        "illegible_scan": "illegible_scan",
        "unsupported_language": "unsupported_language",
        "malformed_table": "malformed_table",
        "unreadable_ocr_portion": "unreadable_ocr_portion",
    }

    for category, expected in categories.items():
        failure_category, _ = map_failure_reason(category)
        assert failure_category == expected

    assert map_failure_reason("illegible_scan", "pages 4-7")[1].startswith("scanned content was unreadable")
    assert map_failure_reason("unsupported_language", "French")[1].startswith("unsupported language segment was detected")
    assert map_failure_reason("malformed_table", "table 2")[1].startswith("table structure was too irregular to extract reliably")
    assert map_failure_reason("unreadable_ocr_portion", "page 3")[1].startswith("OCR could not read a significant portion of the document")
