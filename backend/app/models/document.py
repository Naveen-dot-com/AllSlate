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
    FAILED = "failed"


@dataclass
class ProcessedElement:
    element_id: str
    element_type: str
    page_number: Optional[int] = None
    raw_text: Optional[str] = None
    asset_reference: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Document:
    document_id: str
    filename: str
    file_type: str
    status: ProcessingStatus = ProcessingStatus.UPLOADED
    project_id: Optional[str] = None
    failure_reason: Optional[str] = None
    uploaded_at: Optional[str] = None
    updated_at: Optional[str] = None
    element_count: int = 0
    elements: list[ProcessedElement] = field(default_factory=list)
