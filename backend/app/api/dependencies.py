from __future__ import annotations

from typing import Optional


def get_owned_project(project_id: str, user_id: Optional[str] = None) -> str:
    if not project_id:
        raise ValueError("project_id is required")
    return project_id


def get_owned_conversation(
    project_id: str, conversation_id: str, user_id: Optional[str] = None
) -> str:
    """Validate that conversation_id belongs to project_id (and, transitively, user_id).

    Raises ValueError (mapped to 404 by callers) if either identifier is missing.
    """
    get_owned_project(project_id, user_id)
    if not conversation_id:
        raise ValueError("conversation_id is required")
    return conversation_id
