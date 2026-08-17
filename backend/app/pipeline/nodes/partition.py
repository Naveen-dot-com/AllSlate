from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

from backend.app.config import get_hardening_config
from backend.app.models.document import ProcessedElement
from backend.app.pipeline.confidence import bucket_confidence, bucket_table_regularity


@dataclass
class PartitionResult:
    elements: List[ProcessedElement]


class PartitionProcessor:
    def process(
        self,
        text: str,
        filename: str,
        element_type: str = "text",
        confidence_score: float | None = None,
        table_regularity_score: float | None = None,
        language: Optional[str] = None,
    ) -> PartitionResult:
        if not text.strip():
            return PartitionResult(elements=[])

        confidence = "confident"
        confidence_reason: Optional[str] = None

        if element_type == "table":
            # FR-009: table elements are scored on structural regularity, not raw OCR confidence.
            confidence = "confident" if table_regularity_score is None else bucket_table_regularity(table_regularity_score)
            if confidence != "confident":
                confidence_reason = f"irregular table structure ({confidence})"
        elif confidence_score is not None:
            confidence = bucket_confidence(confidence_score)
            if confidence != "confident":
                confidence_reason = f"low extraction confidence ({confidence})"

        supported_languages = get_hardening_config().supported_languages
        if language and language.strip().lower() not in supported_languages:
            # FR-020/T020: flag unsupported-language segments rather than failing the document.
            confidence = "uncertain" if confidence == "confident" else confidence
            confidence_reason = "unsupported_language_segment"

        parts = [
            ProcessedElement(
                element_id=f"{filename}-1",
                element_type=element_type,
                page_number=1,
                raw_text=text.strip(),
                confidence=confidence,
                confidence_reason=confidence_reason,
            )
        ]
        return PartitionResult(elements=parts)
