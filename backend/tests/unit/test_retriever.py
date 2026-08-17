from __future__ import annotations

from backend.app.rag.retriever import ProjectScopedRetriever, RetrievedChunk


def _chunk(chunk_id: str, project_id: str, score: float) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        document_id=f"doc-{chunk_id}",
        project_id=project_id,
        page_content=f"content for {chunk_id}",
        score=score,
    )


def test_retrieve_excludes_other_projects() -> None:
    retriever = ProjectScopedRetriever(relevance_threshold=0.0)
    candidates = [_chunk("a", "project-1", 0.9), _chunk("b", "project-2", 0.95)]

    results = retriever.retrieve("project-1", "question", candidates)

    assert [c.chunk_id for c in results] == ["a"]


def test_retrieve_filters_below_relevance_threshold() -> None:
    retriever = ProjectScopedRetriever(relevance_threshold=0.5)
    candidates = [_chunk("a", "project-1", 0.1), _chunk("b", "project-1", 0.9)]

    results = retriever.retrieve("project-1", "question", candidates)

    assert [c.chunk_id for c in results] == ["b"]


def test_retrieve_respects_top_k() -> None:
    retriever = ProjectScopedRetriever(relevance_threshold=0.0)
    candidates = [_chunk(str(i), "project-1", i / 10) for i in range(10)]

    results = retriever.retrieve("project-1", "question", candidates, top_k=3)

    assert len(results) == 3
    assert [c.chunk_id for c in results] == ["9", "8", "7"]


def test_retrieve_requires_project_id() -> None:
    retriever = ProjectScopedRetriever()
    try:
        retriever.retrieve("", "question", [])
        assert False, "expected ValueError"
    except ValueError:
        pass
