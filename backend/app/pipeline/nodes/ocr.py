from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from backend.app.pipeline.confidence import bucket_confidence


@dataclass
class OCRResult:
    text: str
    detected: bool = True
    reason: Optional[str] = None
    # FR-009: per-page OCR confidence, computed from the OCR engine's own confidence signal.
    confidence: str = "confident"
    confidence_reason: Optional[str] = None


class OCRProcessor:
    def process(
        self,
        filename: str,
        original_text: str = "",
        confidence_score: float | None = None,
    ) -> OCRResult:
        if not filename.lower().endswith((".png", ".jpg", ".jpeg", ".pdf")):
            return OCRResult(text=original_text, detected=False, reason="File not eligible for OCR")
        if not original_text.strip():
            return OCRResult(
                text="",
                detected=True,
                reason="No readable text recovered",
                confidence="uncertain",
                confidence_reason="no readable text recovered from scan",
            )

        confidence = "confident" if confidence_score is None else bucket_confidence(confidence_score)
        confidence_reason = None if confidence == "confident" else f"low OCR confidence ({confidence})"
        return OCRResult(
            text=original_text.strip(),
            detected=True,
            confidence=confidence,
            confidence_reason=confidence_reason,
        )
