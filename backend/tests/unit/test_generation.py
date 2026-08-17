from __future__ import annotations

import pytest

from backend.app.rag.citations import build_citations
from backend.app.rag.generation import AnswerGenerator, GenerationError, INSUFFICIENT_EVIDENCE_TEXT
from backend.app.rag.context_assembly import assemble_context
from backend.app.rag.retriever import RetrievedChunk


def _chunk(chunk_id: str, asset_reference_id: str | None = None) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        document_id=f"doc-{chunk_id}",
        project_id="project-1",
        page_content=f"content {chunk_id}",
        asset_reference_id=asset_reference_id,
    )


def test_generate_returns_insufficient_evidence_when_no_snippets() -> None:
    generator = AnswerGenerator(llm_call=lambda prompt: "should not be called")

    result = generator.generate("question", [])

    assert result.is_grounded is False
    assert result.content == INSUFFICIENT_EVIDENCE_TEXT
    assert result.contributing_snippet_indices == []


def test_generate_returns_grounded_answer_with_contributing_snippets() -> None:
    snippets = assemble_context([_chunk("a"), _chunk("b")])
    generator = AnswerGenerator(llm_call=lambda prompt: "the answer")

    result = generator.generate("question", snippets)

    assert result.is_grounded is True
    assert result.content == "the answer"
    assert result.contributing_snippet_indices == [1, 2]


def test_generate_raises_generation_error_on_llm_failure() -> None:
    def failing_call(prompt: str) -> str:
        raise RuntimeError("timeout")

    generator = AnswerGenerator(llm_call=failing_call)
    snippets = assemble_context([_chunk("a")])

    with pytest.raises(GenerationError):
        generator.generate("question", snippets)


def test_build_citations_resolves_asset_urls_and_deduplicates() -> None:
    chunks = [_chunk("a", asset_reference_id="asset-1"), _chunk("a", asset_reference_id="asset-1")]

    citations = build_citations(chunks, asset_urls={"asset-1": "https://example/asset-1"})

    assert len(citations) == 1
    assert citations[0].asset_reference_url == "https://example/asset-1"
