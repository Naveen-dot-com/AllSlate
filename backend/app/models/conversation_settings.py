from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

ALL_DOCUMENT_TYPES_SENTINEL = "all"

_VALID_CREATIVITY_LEVELS = {"precise", "balanced", "creative"}
_CREATIVITY_TO_TEMPERATURE = {"precise": 0.2, "balanced": 0.6, "creative": 0.9}

MIN_RETRIEVAL_TOP_K = 1
MAX_RETRIEVAL_TOP_K = 50


class SettingsValidationError(ValueError):
    """Raised when a settings value fails validation (rejected, never clamped)."""


@dataclass
class ConversationSettings:
    conversation_id: str
    web_search_enabled: bool = False
    creativity_level: str = "balanced"
    retrieval_top_k: int = 8
    included_document_types: List[str] = field(
        default_factory=lambda: [ALL_DOCUMENT_TYPES_SENTINEL]
    )
    updated_at: Optional[str] = None

    @property
    def temperature(self) -> float:
        return _CREATIVITY_TO_TEMPERATURE[self.creativity_level]

    def touch(self) -> None:
        self.updated_at = datetime.now(timezone.utc).isoformat()


def validate_creativity_level(value: str) -> str:
    if value not in _VALID_CREATIVITY_LEVELS:
        raise SettingsValidationError(
            f"creativity_level must be one of {sorted(_VALID_CREATIVITY_LEVELS)}"
        )
    return value


def validate_retrieval_top_k(value: int) -> int:
    if not (MIN_RETRIEVAL_TOP_K <= value <= MAX_RETRIEVAL_TOP_K):
        raise SettingsValidationError(
            f"retrieval_top_k must be between {MIN_RETRIEVAL_TOP_K} and {MAX_RETRIEVAL_TOP_K}"
        )
    return value


def validate_included_document_types(value: List[str]) -> List[str]:
    if not value:
        raise SettingsValidationError(
            "included_document_types must not be empty; use "
            f"'{ALL_DOCUMENT_TYPES_SENTINEL}' to include every type"
        )
    return value
