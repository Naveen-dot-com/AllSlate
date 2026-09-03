from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from backend.app.services.document_store import document_store

router = APIRouter(prefix="/api/v1/projects", tags=["status"])


@router.get("/{project_id}/documents/status-stream")
async def status_stream(project_id: str):
    async def event_generator():
        cursor = 0
        idle_cycles = 0
        while idle_cycles < 300:
            events = document_store.events[project_id]
            while cursor < len(events):
                event = events[cursor]
                cursor += 1
                yield "event: status\ndata: " + json.dumps(
                    {
                        "document_id": event.document_id,
                        "stage": event.stage.value,
                        "occurred_at": event.occurred_at,
                        "reason": event.reason,
                        "failure_category": event.failure_category,
                    }
                ) + "\n\n"
                idle_cycles = 0
            idle_cycles += 1
            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
