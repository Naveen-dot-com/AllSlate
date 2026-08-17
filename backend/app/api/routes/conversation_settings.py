from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.models.conversation_settings import SettingsValidationError
from backend.app.services.settings_service import SettingsService

router = APIRouter(prefix="/api/v1/projects", tags=["conversation-settings"])

_settings_service = SettingsService()


def get_settings_service() -> SettingsService:
    """Shared accessor so other routes (e.g. chat.py) read the same store."""
    return _settings_service


class UpdateSettingsRequest(BaseModel):
    web_search_enabled: bool | None = None
    creativity_level: str | None = None
    retrieval_top_k: int | None = None
    included_document_types: list[str] | None = None


def _serialize(settings) -> Dict[str, Any]:
    return {
        "web_search_enabled": settings.web_search_enabled,
        "creativity_level": settings.creativity_level,
        "retrieval_top_k": settings.retrieval_top_k,
        "included_document_types": settings.included_document_types,
        "updated_at": settings.updated_at,
    }


@router.get("/{project_id}/conversations/{conversation_id}/settings")
async def get_settings(project_id: str, conversation_id: str) -> Dict[str, Any]:
    if not project_id or not conversation_id:
        raise HTTPException(status_code=404, detail="conversation not found")
    settings = _settings_service.get_or_create(conversation_id)
    return _serialize(settings)


@router.patch("/{project_id}/conversations/{conversation_id}/settings")
async def update_settings(
    project_id: str, conversation_id: str, body: UpdateSettingsRequest
) -> Dict[str, Any]:
    if not project_id or not conversation_id:
        raise HTTPException(status_code=404, detail="conversation not found")
    try:
        settings = _settings_service.update(
            conversation_id,
            web_search_enabled=body.web_search_enabled,
            creativity_level=body.creativity_level,
            retrieval_top_k=body.retrieval_top_k,
            included_document_types=body.included_document_types,
        )
    except SettingsValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _serialize(settings)
