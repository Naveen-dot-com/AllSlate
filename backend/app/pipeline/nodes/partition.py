from __future__ import annotations

from dataclasses import dataclass
from typing import List

from backend.app.models.document import ProcessedElement


@dataclass
class PartitionResult:
    elements: List[ProcessedElement]


class PartitionProcessor:
    def process(self, text: str, filename: str) -> PartitionResult:
        if not text.strip():
            return PartitionResult(elements=[])

        parts = [
            ProcessedElement(
                element_id=f"{filename}-1",
                element_type="text",
                page_number=1,
                raw_text=text.strip(),
            )
        ]
        return PartitionResult(elements=parts)
