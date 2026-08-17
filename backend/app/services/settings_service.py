from __future__ import annotations

from typing import Dict

from backend.app.models.conversation_settings import (
    ConversationSettings,
    validate_creativity_level,
    validate_included_document_types,
    validate_retrieval_top_k,
)


class SettingsService:
    """Per-conversation settings store with default-on-first-read behavior.

    Every conversation thread always has a well-defined settings row: reading
    settings for a thread that has none yet creates and persists the defaults
    (data-model.md Cross-Cutting Rules), so no thread ever falls back to
    undocumented implicit defaults.
    """

    def __init__(self) -> None:
        self._settings: Dict[str, ConversationSettings] = {}

    def get_or_create(self, conversation_id: str) -> ConversationSettings:
        settings = self._settings.get(conversation_id)
        if settings is None:
            settings = ConversationSettings(conversation_id=conversation_id)
            settings.touch()
            self._settings[conversation_id] = settings
        return settings

    def update(
        self,
        conversation_id: str,
        *,
        web_search_enabled: bool | None = None,
        creativity_level: str | None = None,
        retrieval_top_k: int | None = None,
        included_document_types: list[str] | None = None,
    ) -> ConversationSettings:
        """Validate then persist a partial update.

        Validation happens before any field is mutated, so a rejected change
        leaves the previously persisted, valid settings fully intact.
        """
        current = self.get_or_create(conversation_id)

        if creativity_level is not None:
            validate_creativity_level(creativity_level)
        if retrieval_top_k is not None:
            validate_retrieval_top_k(retrieval_top_k)
        if included_document_types is not None:
            validate_included_document_types(included_document_types)

        if web_search_enabled is not None:
            current.web_search_enabled = web_search_enabled
        if creativity_level is not None:
            current.creativity_level = creativity_level
        if retrieval_top_k is not None:
            current.retrieval_top_k = retrieval_top_k
        if included_document_types is not None:
            current.included_document_types = included_document_types

        current.touch()
        return current

    def snapshot(self, conversation_id: str) -> ConversationSettings:
        """Resolve settings once, at ask-time, for use as an effective-settings snapshot.

        Returns a detached copy so a later mid-flight settings change can never
        mutate an in-progress answer's captured configuration (FR-013).
        """
        current = self.get_or_create(conversation_id)
        return ConversationSettings(
            conversation_id=current.conversation_id,
            web_search_enabled=current.web_search_enabled,
            creativity_level=current.creativity_level,
            retrieval_top_k=current.retrieval_top_k,
            included_document_types=list(current.included_document_types),
            updated_at=current.updated_at,
        )
