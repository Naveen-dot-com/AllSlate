from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class OCRResult:
    text: str
    detected: bool = True
    reason: Optional[str] = None


class OCRProcessor:
    def process(self, filename: str, original_text: str = "") -> OCRResult:
        if not filename.lower().endswith((".png", ".jpg", ".jpeg", ".pdf")):
            return OCRResult(text=original_text, detected=False, reason="File not eligible for OCR")
        if not original_text.strip():
            return OCRResult(text="", detected=True, reason="No readable text recovered")
        return OCRResult(text=original_text.strip(), detected=True)
