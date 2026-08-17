from __future__ import annotations

from typing import Optional


def get_owned_project(project_id: str, user_id: Optional[str] = None) -> str:
    if not project_id:
        raise ValueError("project_id is required")
    return project_id
