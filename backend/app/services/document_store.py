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
        self.file_bytes: Dict[str, bytes] = {}
        self.events: DefaultDict[str, List[StatusEvent]] = defaultdict(list)

    def add(self, document: Document) -> None:
        self.documents[document.document_id] = document

    def store_file(self, document_id: str, content: bytes) -> None:
        self.file_bytes[document_id] = content

    def get_file(self, project_id: str, document_id: str) -> bytes | None:
        document = self.documents.get(document_id)
        if document is None or document.project_id != project_id:
            return None
        return self.file_bytes.get(document_id)

    def delete(self, project_id: str, document_id: str) -> bool:
        document = self.documents.get(document_id)
        if document is None or document.project_id != project_id:
            return False
        self.documents.pop(document_id, None)
        self.file_bytes.pop(document_id, None)
        return True

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
            raw_text = text.strip()
            if not raw_text:
                self.update_status(document, ProcessingStatus.PARTITIONING, "No readable text could be extracted from the uploaded file.")
                await asyncio.sleep(0.2)
                self.update_status(document, ProcessingStatus.FAILED, "No readable text could be extracted from the uploaded file.", "other")
                return

            for status in (ProcessingStatus.PARTITIONING, ProcessingStatus.CHUNKING, ProcessingStatus.SUMMARIZING, ProcessingStatus.VECTORIZING):
                self.update_status(document, status)
                await asyncio.sleep(0.4)

            paragraphs = [segment.strip() for segment in raw_text.replace("\r\n", "\n").split("\n\n") if segment.strip()]
            if not paragraphs:
                paragraphs = [raw_text]

            chunk_size = max(180, len(raw_text) // max(1, min(4, len(paragraphs))))
            chunks: list[str] = []
            for paragraph in paragraphs:
                if len(paragraph) <= chunk_size:
                    chunks.append(paragraph)
                    continue
                for index in range(0, len(paragraph), chunk_size):
                    chunk = paragraph[index:index + chunk_size].strip()
                    if chunk:
                        chunks.append(chunk)

            if not chunks:
                chunks = [raw_text]

            document.elements = [
                ProcessedElement(
                    f"{document.document_id}-element-{index}",
                    "text",
                    (index % 3) + 1,
                    chunk,
                    confidence="confident" if index < len(chunks) else "partial",
                    confidence_reason=None if index < len(chunks) else "Chunk boundaries were inferred from the extracted text.",
                )
                for index, chunk in enumerate(chunks[:8], start=1)
            ]
            document.element_count = len(document.elements)
            outcome = resolve_document_outcome(document.document_id, [{"confidence": element.confidence} for element in document.elements])
            self.update_status(document, outcome.current_status, outcome.failure_reason, outcome.failure_category)
        except Exception as exc:
            self.update_status(document, ProcessingStatus.FAILED, f"Processing failed: {exc}", "other")


document_store = DocumentStore()