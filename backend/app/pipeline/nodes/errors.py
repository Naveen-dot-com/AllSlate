from __future__ import annotations

from typing import Any

FAILURE_CATEGORY_MAP = {
    "illegible_scan": "illegible_scan",
    "unsupported_language": "unsupported_language",
    "malformed_table": "malformed_table",
    "unreadable_ocr_portion": "unreadable_ocr_portion",
    "other": "other",
}


def map_failure_reason(category: str, context: str | None = None) -> tuple[str, str]:
    normalized = category.strip().lower()
    context_text = f" {context}" if context else ""

    if normalized == "illegible_scan":
        return ("illegible_scan", f"scanned content was unreadable{context_text}.")
    if normalized == "unsupported_language":
        return ("unsupported_language", f"unsupported language segment was detected{context_text}.")
    if normalized == "malformed_table":
        return ("malformed_table", f"table structure was too irregular to extract reliably{context_text}.")
    if normalized == "unreadable_ocr_portion":
        return ("unreadable_ocr_portion", f"OCR could not read a significant portion of the document{context_text}.")
    return ("other", f"processing failed{context_text}.")
