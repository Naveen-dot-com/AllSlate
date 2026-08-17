from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from backend.app.models.message import Message, MessageCitation, MessageStatus
from backend.app.rag.citations import build_citations
from backend.app.rag.context_assembly import assemble_context
from backend.app.rag.generation import AnswerGenerator, GenerationError
from backend.app.rag.retriever import ProjectScopedRetriever, RetrievedChunk

PhaseCallback = Callable[[str], None]


@dataclass
class AskResult:
    content: str
    status: MessageStatus
    is_grounded: bool
    citations: List[MessageCitation] = field(default_factory=list)
    failure_reason: Optional[str] = None


class RagChatGraph:
    """Orchestrates retrieval -> context assembly -> generation -> citations.

    Mirrors the staged, node-like structure of the ingestion pipeline's
    `PipelineGraph` (002-document-processing-pipeline) for a query-time
    concern, emitting `retrieving`/`generating` phase events along the way.
    """

    def __init__(
        self,
        retriever: Optional[ProjectScopedRetriever] = None,
        generator: Optional[AnswerGenerator] = None,
    ) -> None:
        self.retriever = retriever or ProjectScopedRetriever()
        self.generator = generator or AnswerGenerator()

    def ask(
        self,
        project_id: str,
        question: str,
        candidates: List[RetrievedChunk],
        top_k: int = 8,
        on_phase: Optional[PhaseCallback] = None,
    ) -> AskResult:
        if on_phase:
            on_phase("retrieving")
        retrieved = self.retriever.retrieve(project_id, question, candidates, top_k=top_k)

        if on_phase:
            on_phase("generating")
        snippets = assemble_context(retrieved)

        try:
            generation = self.generator.generate(question, snippets)
        except GenerationError as exc:
            return AskResult(
                content="",
                status=MessageStatus.FAILED,
                is_grounded=False,
                failure_reason=str(exc),
            )

        contributing = [
            retrieved[i - 1] for i in generation.contributing_snippet_indices
        ]
        citations = build_citations(contributing)

        return AskResult(
            content=generation.content,
            status=MessageStatus.COMPLETE,
            is_grounded=generation.is_grounded,
            citations=citations,
        )
