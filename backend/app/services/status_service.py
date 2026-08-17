from __future__ import annotations

from typing import Dict, List, Optional

from backend.app.models.document import ProcessingStatus


class StatusService:
    def get_latest_status(self, document_id: str, statuses: Optional[Dict[str, ProcessingStatus]] = None) -> ProcessingStatus:
        statuses = statuses or {}
        return statuses.get(document_id, ProcessingStatus.UPLOADED)

    def get_current_stage(self, document_id: str, stages: Optional[Dict[str, ProcessingStatus]] = None) -> ProcessingStatus:
        return self.get_latest_status(document_id, stages)

    def aggregate_statuses(self, document_ids: List[str], statuses: Dict[str, ProcessingStatus]) -> Dict[str, ProcessingStatus]:
        return {document_id: statuses.get(document_id, ProcessingStatus.UPLOADED) for document_id in document_ids}
