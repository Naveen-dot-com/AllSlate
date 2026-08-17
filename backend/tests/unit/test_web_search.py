from __future__ import annotations

from backend.app.rag.retriever import RetrievedChunk
from backend.app.rag.web_search import WebSearchNode


def _web_chunk(chunk_id: str) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        document_id="web",
        project_id="project-1",
        page_content=f"web result {chunk_id}",
    )


def test_web_search_disabled_makes_no_search_call() -> None:
    calls: list[str] = []

    def search(question: str):
        calls.append(question)
        return [_web_chunk("1")]

    node = WebSearchNode(search_call=search)

    outcome = node.run("question", web_search_enabled=False)

    assert calls == []
    assert outcome.attempted is False
    assert outcome.chunks == []


def test_web_search_enabled_tags_results_as_web_source() -> None:
    node = WebSearchNode(search_call=lambda q: [_web_chunk("1")])

    outcome = node.run("question", web_search_enabled=True)

    assert outcome.attempted is True
    assert outcome.failed is False
    assert [c.element_type for c in outcome.chunks] == ["web"]


def test_web_search_failure_falls_back_gracefully() -> None:
    def failing_search(question: str):
        raise RuntimeError("timeout")

    node = WebSearchNode(search_call=failing_search)

    outcome = node.run("question", web_search_enabled=True)

    assert outcome.failed is True
    assert outcome.chunks == []


def test_web_search_bounds_result_count() -> None:
    node = WebSearchNode(
        search_call=lambda q: [_web_chunk(str(i)) for i in range(10)], max_results=2
    )

    outcome = node.run("question", web_search_enabled=True)

    assert len(outcome.chunks) == 2
