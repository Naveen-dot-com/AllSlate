from __future__ import annotations

from backend.app.models.message import MessageStatus
from backend.app.rag.graph import RagChatGraph
from backend.app.rag.generation import AnswerGenerator
from backend.app.rag.retriever import ProjectScopedRetriever, RetrievedChunk


def _chunk(chunk_id: str, project_id: str, score: float = 0.9) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        document_id=f"doc-{chunk_id}",
        project_id=project_id,
        page_content=f"relevant content for {chunk_id}",
        score=score,
    )


def test_ask_returns_grounded_answer_with_citations() -> None:
    graph = RagChatGraph(generator=AnswerGenerator(llm_call=lambda prompt: "grounded answer"))
    candidates = [_chunk("a", "project-1"), _chunk("b", "project-2")]

    phases: list[str] = []
    result = graph.ask("project-1", "what is X?", candidates, on_phase=phases.append)

    assert phases == ["retrieving", "generating"]
    assert result.status == MessageStatus.COMPLETE
    assert result.is_grounded is True
    assert [c.chunk_id for c in result.citations] == ["a"]


def test_ask_returns_insufficient_evidence_when_no_relevant_chunks() -> None:
    graph = RagChatGraph(retriever=ProjectScopedRetriever(relevance_threshold=0.99))

    result = graph.ask("project-1", "what is X?", [_chunk("a", "project-1", score=0.1)])

    assert result.status == MessageStatus.COMPLETE
    assert result.is_grounded is False
    assert result.citations == []


def test_ask_never_returns_citations_from_other_projects() -> None:
    graph = RagChatGraph(generator=AnswerGenerator(llm_call=lambda prompt: "answer"))
    candidates = [_chunk("cross-project", "project-2", score=0.99)]

    result = graph.ask("project-1", "question", candidates)

    assert result.citations == []
    assert result.is_grounded is False


def test_ask_surfaces_failure_without_raising() -> None:
    def failing_call(prompt: str) -> str:
        raise RuntimeError("upstream timeout")

    graph = RagChatGraph(generator=AnswerGenerator(llm_call=failing_call))

    result = graph.ask("project-1", "question", [_chunk("a", "project-1")])

    assert result.status == MessageStatus.FAILED
    assert result.failure_reason == "upstream timeout"
