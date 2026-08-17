from __future__ import annotations

from backend.app.services.conversation_service import ConversationService
from backend.app.services.message_service import MessageService


def test_conversation_service_get_owned_rejects_cross_project_access() -> None:
    service = ConversationService()
    conversation = service.create("project-1")

    try:
        service.get_owned("project-2", conversation.id)
        assert False, "expected KeyError"
    except KeyError:
        pass

    assert service.get_owned("project-1", conversation.id).id == conversation.id


def test_message_service_assigns_strictly_increasing_sequence_numbers() -> None:
    service = MessageService()
    conversation_id = "conv-1"

    first = service.append_user_message(conversation_id, "question 1")
    second = service.append_assistant_message(conversation_id)
    third = service.append_user_message(conversation_id, "question 2")

    assert [m.sequence_number for m in (first, second, third)] == [1, 2, 3]
    assert [m.sequence_number for m in service.history(conversation_id)] == [1, 2, 3]


def test_message_service_rejects_empty_question() -> None:
    service = MessageService()
    try:
        service.append_user_message("conv-1", "   ")
        assert False, "expected ValueError"
    except ValueError:
        pass
