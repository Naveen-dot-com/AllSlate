from __future__ import annotations

from dataclasses import dataclass
from typing import List

from backend.app.rag.retriever import RetrievedChunk


@dataclass
class ContextSnippet:
    index: int
    chunk_id: str
    text: str


def assemble_context(chunks: List[RetrievedChunk]) -> List[ContextSnippet]:
    """Turn retrieved chunks into indexed, clearly delimited context snippets.

    Each snippet is tagged with a stable index so the backend (not the model's
    free-text output) authoritatively determines which chunks backed the
    final answer.
    """
    return [
        ContextSnippet(index=i, chunk_id=chunk.chunk_id, text=chunk.page_content)
        for i, chunk in enumerate(chunks, start=1)
    ]


def format_prompt(question: str, snippets: List[ContextSnippet]) -> str:
    if not snippets:
        return question

    context_block = "\n".join(f"[{s.index}] {s.text}" for s in snippets)
    return (
        "Answer only using the numbered context below. Reference snippet "
        "numbers you relied on.\n\n"
        f"Context:\n{context_block}\n\nQuestion: {question}"
    )
