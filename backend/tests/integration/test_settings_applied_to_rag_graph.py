from __future__ import annotations

from backend.app.models.conversation_settings import ConversationSettings
from backend.app.models.message import MessageStatus
from backend.app.rag.graph import RagChatGraph
from backend.app.rag.generation import AnswerGenerator
from backend.app.rag.retriever import RetrievedChunk
from backend.app.rag.web_search import WebSearchNode


def _chunk(chunk_id: str, project_id: str, element_type: str = "text", score: float = 0.9):
    return RetrievedChunk(
        chunk_id=chunk_id,
        document_id=f"doc-{chunk_id}",
        project_id=project_id,
        page_content=f"content {chunk_id}",
        element_type=element_type,
        score=score,
    )


def test_web_search_off_never_includes_web_citations() -> None:
    graph = RagChatGraph(
        generator=AnswerGenerator(llm_call=lambda p: "answer"),
        web_search_node=WebSearchNode(search_call=lambda q: [_chunk("web-1", "project-1")]),
    )
    settings = ConversationSettings(conversation_id="conv-1", web_search_enabled=False)

    result = graph.ask("project-1", "question", [_chunk("a", "project-1")], settings=settings)

    assert result.used_web_search is False
    assert all(c.document_id != "doc-web-1" for c in result.citations)


def test_web_search_on_can_include_web_result() -> None:
    graph = RagChatGraph(
        generator=AnswerGenerator(llm_call=lambda p: "answer"),
        web_search_node=WebSearchNode(search_call=lambda q: [_chunk("web-1", "project-1")]),
    )
    settings = ConversationSettings(conversation_id="conv-1", web_search_enabled=True)

    result = graph.ask("project-1", "question", [_chunk("a", "project-1")], settings=settings)

    assert result.used_web_search is True
    assert any(c.document_id == "doc-web-1" for c in result.citations)


def test_document_type_filter_narrows_citations() -> None:
    graph = RagChatGraph(generator=AnswerGenerator(llm_call=lambda p: "answer"))
    settings = ConversationSettings(
        conversation_id="conv-1", included_document_types=["table"]
    )
    candidates = [_chunk("text-1", "project-1", element_type="text"),
                  _chunk("table-1", "project-1", element_type="table")]

    result = graph.ask("project-1", "question", candidates, settings=settings)

    assert [c.document_id for c in result.citations] == ["doc-table-1"]


def test_retrieval_top_k_bounds_number_of_citations() -> None:
    graph = RagChatGraph(generator=AnswerGenerator(llm_call=lambda p: "answer"))
    settings = ConversationSettings(conversation_id="conv-1", retrieval_top_k=1)
    candidates = [_chunk(str(i), "project-1") for i in range(5)]

    result = graph.ask("project-1", "question", candidates, settings=settings)

    assert len(result.citations) == 1


def test_creativity_level_maps_to_temperature_used_in_generation() -> None:
    seen_temperatures: list[float] = []

    def capture_temperature(question, snippets, temperature=0.6):
        seen_temperatures.append(temperature)
        return AnswerGenerator(llm_call=lambda p: "answer").generate(
            question, snippets, temperature=temperature
        )

    graph = RagChatGraph(generator=AnswerGenerator(llm_call=lambda p: "answer"))
    settings = ConversationSettings(conversation_id="conv-1", creativity_level="creative")

    result = graph.ask(
        "project-1", "question", [_chunk("a", "project-1")], settings=settings
    )

    assert result.status == MessageStatus.COMPLETE
