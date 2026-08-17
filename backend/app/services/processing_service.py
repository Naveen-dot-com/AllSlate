from __future__ import annotations

from dataclasses import dataclass
from typing import List

from backend.app.models.document import Document, ProcessingStatus


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
            job.document.status = ProcessingStatus.STORED
        return list(self._jobs)
