from __future__ import annotations

from dataclasses import dataclass
from typing import List

from backend.app.models.document import Document, ProcessingStatus
from backend.app.pipeline.graph import resolve_document_outcome


@dataclass
class ProcessingJob:
    document: Document
    queue_name: str = "document-processing"


class ProcessingService:
    def __init__(self) -> None:
        self._jobs: List[ProcessingJob] = []

    def enqueue(self, document: Document) -> ProcessingJob:
        job = ProcessingJob(document=document)
        self._jobs.append(job)
        document.status = ProcessingStatus.QUEUED
        return job

    def process_all(self) -> List[ProcessingJob]:
        for job in self._jobs:
            document = job.document
            elements = [
                {"confidence": element.confidence} for element in document.elements
            ]
            outcome = resolve_document_outcome(document.document_id, elements)
            document.status = outcome.current_status
            document.failure_reason = outcome.failure_reason
            document.failure_category = outcome.failure_category
        return list(self._jobs)
