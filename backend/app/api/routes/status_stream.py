from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from backend.app.models.document import ProcessingStatus

router = APIRouter(prefix="/api/v1/projects", tags=["status"])


@router.get("/{project_id}/documents/status-stream")
async def status_stream(project_id: str):
    def event_generator():
        yield "event: status\ndata: {\"document_id\": \"demo-doc\", \"stage\": \"queued\", \"occurred_at\": \"now\"}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
