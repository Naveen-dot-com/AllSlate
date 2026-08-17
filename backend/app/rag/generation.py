from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from backend.app.rag.context_assembly import ContextSnippet, format_prompt

INSUFFICIENT_EVIDENCE_TEXT = (
    "I don't have enough information in this project's documents to answer that."
)


@dataclass
class GenerationResult:
    content: str
    is_grounded: bool
    contributing_snippet_indices: List[int] = field(default_factory=list)
    temperature_used: float = 0.6


class GenerationError(Exception):
    """Raised when the generation call fails or times out (FR-016)."""


class AnswerGenerator:
    """Wraps the Gemini chat/generation call.

    Kept as a thin, swappable seam: callers inject a `llm_call` function (the
    real Gemini client in production, a fake/deterministic one in tests) so
    generation logic can be unit-tested without network access.
    """

    def __init__(self, llm_call=None) -> None:
        self._llm_call = llm_call or self._default_llm_call

    @staticmethod
    def _default_llm_call(prompt: str) -> str:
        raise GenerationError("No LLM client configured")

    def generate(
        self,
        question: str,
        snippets: List[ContextSnippet],
        temperature: float = 0.6,
    ) -> GenerationResult:
        if not snippets:
            return GenerationResult(
                content=INSUFFICIENT_EVIDENCE_TEXT,
                is_grounded=False,
                contributing_snippet_indices=[],
                temperature_used=temperature,
            )

        prompt = format_prompt(question, snippets)
        try:
            answer_text = self._llm_call(prompt)
        except Exception as exc:  # noqa: BLE001 - surfaced as a graceful failure
            raise GenerationError(str(exc)) from exc

        return GenerationResult(
            content=answer_text,
            is_grounded=True,
            contributing_snippet_indices=[s.index for s in snippets],
            temperature_used=temperature,
        )
