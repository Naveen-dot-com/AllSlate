from __future__ import annotations

import pytest

from backend.app.models.conversation_settings import SettingsValidationError
from backend.app.services.settings_service import SettingsService


def test_get_or_create_returns_sensible_defaults() -> None:
    service = SettingsService()

    settings = service.get_or_create("conv-1")

    assert settings.web_search_enabled is False
    assert settings.creativity_level == "balanced"
    assert settings.retrieval_top_k == 8
    assert settings.included_document_types == ["all"]


def test_update_rejects_empty_document_type_list_and_keeps_previous_value() -> None:
    service = SettingsService()
    service.update("conv-1", included_document_types=["text", "table"])

    with pytest.raises(SettingsValidationError):
        service.update("conv-1", included_document_types=[])

    assert service.get_or_create("conv-1").included_document_types == ["text", "table"]


def test_update_rejects_out_of_range_top_k_without_clamping() -> None:
    service = SettingsService()

    with pytest.raises(SettingsValidationError):
        service.update("conv-1", retrieval_top_k=0)
    with pytest.raises(SettingsValidationError):
        service.update("conv-1", retrieval_top_k=51)

    assert service.get_or_create("conv-1").retrieval_top_k == 8


def test_update_rejects_unknown_creativity_level() -> None:
    service = SettingsService()

    with pytest.raises(SettingsValidationError):
        service.update("conv-1", creativity_level="unhinged")


def test_snapshot_is_detached_from_later_updates() -> None:
    service = SettingsService()
    service.update("conv-1", web_search_enabled=True)

    snapshot = service.snapshot("conv-1")
    service.update("conv-1", web_search_enabled=False)

    assert snapshot.web_search_enabled is True
    assert service.get_or_create("conv-1").web_search_enabled is False


def test_scoping_is_independent_per_conversation() -> None:
    service = SettingsService()
    service.update("conv-1", web_search_enabled=True)

    assert service.get_or_create("conv-2").web_search_enabled is False
