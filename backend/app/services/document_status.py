from __future__ import annotations

from typing import Iterable

from backend.app.config import get_hardening_config
from backend.app.pipeline.confidence import bucket_confidence


def _normalize_confidence(value: object) -> str:
    if value is None:
        return "uncertain"

    if isinstance(value, str):
        normalized = value.strip().lower()
        if not normalized:
            return "uncertain"
        if normalized in {"confident", "partial", "uncertain"}:
            return normalized
        try:
            return bucket_confidence(float(normalized))
        except ValueError:
            return "uncertain"

    return bucket_confidence(value)


def summarize_document_status(elements: Iterable[dict] | None) -> tuple[str, str | None, bool]:
    items = list(elements or [])
    if not items:
        return ("stored", None, False)

    total = len(items)
    weak_count = sum(1 for item in items if _normalize_confidence(item.get("confidence")) != "confident")
    threshold = get_hardening_config().partial_vs_fail_threshold

    if weak_count == 0:
        return ("stored", None, False)

    if weak_count / total <= threshold:
        return ("stored_partial", "partial content detected", True)

    return ("failed", "too much content was low confidence or unreadable", True)


def has_low_confidence_content(elements: Iterable[dict] | None) -> bool:
    return summarize_document_status(elements)[2]
