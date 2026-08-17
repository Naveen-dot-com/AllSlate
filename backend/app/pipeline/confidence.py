from __future__ import annotations

from typing import Literal

from backend.app.config import get_hardening_config

ConfidenceBucket = Literal["confident", "partial", "uncertain"]


def _coerce_score(score: float | int | str | None) -> float | None:
    if score is None:
        return None

    if isinstance(score, bool):
        return float(score)

    if isinstance(score, str):
        normalized = score.strip().lower()
        if normalized in {"confident", "partial", "uncertain"}:
            return {"confident": 1.0, "partial": 0.7, "uncertain": 0.0}[normalized]
        if normalized == "":
            return None
        score = normalized

    try:
        value = float(score)
    except (TypeError, ValueError):
        return None

    return max(0.0, min(1.0, value))


def bucket_confidence(score: float | int | str | None) -> ConfidenceBucket:
    if score is None:
        return "uncertain"

    config = get_hardening_config()
    score_value = _coerce_score(score)
    if score_value is None:
        return "uncertain"

    if score_value >= config.ocr_confidence_partial_threshold:
        return "confident"
    if score_value >= config.ocr_confidence_uncertain_threshold:
        return "partial"
    return "uncertain"


def bucket_table_regularity(score: float | int | str | None) -> ConfidenceBucket:
    if score is None:
        return "uncertain"

    config = get_hardening_config()
    score_value = _coerce_score(score)
    if score_value is None:
        return "uncertain"

    if score_value >= config.table_regularity_partial_threshold:
        return "confident"
    if score_value >= config.table_regularity_uncertain_threshold:
        return "partial"
    return "uncertain"
