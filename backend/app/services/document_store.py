from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import datetime, timezone
from typing import DefaultDict, Dict, List

from backend.app.models.document import Document, ProcessedElement, ProcessingStatus
from backend.app.pipeline.graph import resolve_document_outcome
from backend.app.pipeline.status_events import StatusEvent


class DocumentStore:
    """Project-scoped runtime storage used until persistent storage is configured."""

    def __init__(self) -> None:
        self.documents: Dict[str, Document] = {}
        self.events: DefaultDict[str, List[StatusEvent]] = defaultdict(list)

    def add(self, document: Document) -> None:
        self.documents[document.document_id] = document

    def list(self, project_id: str) -> List[Document]:
        return [document for document in self.documents.values() if document.project_id == project_id]

    def get(self, project_id: str, document_id: str) -> Document | None:
        document = self.documents.get(document_id)
        return document if document and document.project_id == project_id else None

    def update_status(self, document: Document, status: ProcessingStatus, reason: str | None = None, failure_category: str | None = None) -> None:
        document.status = status
        document.failure_reason = reason
        document.failure_category = failure_category
        document.updated_at = datetime.now(timezone.utc).isoformat()
        self.events[document.project_id or ""].append(StatusEvent(document.document_id, status, document.updated_at, reason, failure_category))

    async def process(self, document: Document, text: str) -> None:
        try:
            for status in (ProcessingStatus.PARTITIONING, ProcessingStatus.CHUNKING, ProcessingStatus.SUMMARIZING, ProcessingStatus.VECTORIZING):
                self.update_status(document, status)
                await asyncio.sleep(0.2)
            extracted_text = text.strip() or "No readable text could be extracted from this document."
            confidence = "confident" if text.strip() else "uncertain"
            reason = None if text.strip() else "No readable text was recovered from the uploaded file."
            document.elements = [ProcessedElement(f"{document.document_id}-element-1", "text", 1, extracted_text, confidence=confidence, confidence_reason=reason)]
            document.element_count = len(document.elements)
            outcome = resolve_document_outcome(document.document_id, [{"confidence": element.confidence} for element in document.elements])
            self.update_status(document, outcome.current_status, outcome.failure_reason, outcome.failure_category)
        except Exception as exc:
            self.update_status(document, ProcessingStatus.FAILED, f"Processing failed: {exc}", "other")


document_store = DocumentStore()