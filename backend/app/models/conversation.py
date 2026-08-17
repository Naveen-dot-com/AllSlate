from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Conversation:
    id: str
    project_id: str
    title: Optional[str] = None
    created_at: Optional[str] = None
