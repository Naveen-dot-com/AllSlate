from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from backend.app.models.document import ProcessedElement


@dataclass
class ChunkRecord:
    chunk_id: str
    document_id: str
    element_id: str
    page_content: str
    element_type: str
    page_number: Optional[int]
    asset_reference: Optional[str] = None
    metadata: Dict[str, Any] | None = None


class ChunkBuilder:
    def build(self, document_id: str, elements: List[ProcessedElement]) -> List[ChunkRecord]:
        records: List[ChunkRecord] = []
        for index, element in enumerate(elements):
            content = element.raw_text or "summary"
            records.append(
                ChunkRecord(
                    chunk_id=f"{document_id}-chunk-{index}",
                    document_id=document_id,
                    element_id=element.element_id,
                    page_content=content,
                    element_type=element.element_type,
                    page_number=element.page_number,
                    asset_reference=element.asset_reference,
                    metadata={"source": document_id, "element_type": element.element_type},
                )
            )
        return records
