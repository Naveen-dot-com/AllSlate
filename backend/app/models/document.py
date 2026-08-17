from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class ProcessingStatus(str, Enum):
    UPLOADED = "uploaded"
    QUEUED = "queued"
    PARTITIONING = "partitioning"
    CHUNKING = "chunking"
    SUMMARIZING = "summarizing"
    VECTORIZING = "vectorizing"
    STORED = "stored"
    STORED_PARTIAL = "stored_partial"
    FAILED = "failed"


# FR-014: distinguishable, specific failure categories for partition/OCR failures.
FAILURE_CATEGORIES = (
    "illegible_scan",
    "unreadable_ocr_portion",
    "malformed_table",
    "unsupported_language",
    "other",
)


@dataclass
class ProcessedElement:
    element_id: str
    element_type: str
    page_number: Optional[int] = None
    raw_text: Optional[str] = None
    asset_reference: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    # FR-009: confidence/confidence_reason surface OCR/table-extraction certainty per element.
    confidence: str = "confident"
    confidence_reason: Optional[str] = None


@dataclass
class Document:
    document_id: str
    filename: str
    file_type: str
    status: ProcessingStatus = ProcessingStatus.UPLOADED
    project_id: Optional[str] = None
    failure_reason: Optional[str] = None
    # FR-014: one of FAILURE_CATEGORIES, set only when status is FAILED.
    failure_category: Optional[str] = None
    uploaded_at: Optional[str] = None
    updated_at: Optional[str] = None
    element_count: int = 0
    elements: list[ProcessedElement] = field(default_factory=list)
