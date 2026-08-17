from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from backend.app.models.conversation_settings import (
    ALL_DOCUMENT_TYPES_SENTINEL,
    ConversationSettings,
)
from backend.app.models.message import Message, MessageCitation, MessageStatus
from backend.app.rag.citations import build_citations
from backend.app.rag.context_assembly import assemble_context
from backend.app.rag.generation import AnswerGenerator, GenerationError
from backend.app.rag.retriever import ProjectScopedRetriever, RetrievedChunk
from backend.app.rag.web_search import WebSearchNode

PhaseCallback = Callable[[str], None]


@dataclass
class AskResult:
    content: str
    status: MessageStatus
    is_grounded: bool
    citations: List[MessageCitation] = field(default_factory=list)
    failure_reason: Optional[str] = None
    used_web_search: bool = False


def _filter_by_document_type(
    candidates: List[RetrievedChunk], included_document_types: List[str]
) -> List[RetrievedChunk]:
    if ALL_DOCUMENT_TYPES_SENTINEL in included_document_types:
        return candidates
    return [c for c in candidates if c.element_type in included_document_types]


class RagChatGraph:
    """Orchestrates retrieval -> web search -> context assembly -> generation -> citations.

    Mirrors the staged, node-like structure of the ingestion pipeline's
    `PipelineGraph` (002-document-processing-pipeline) for a query-time
    concern, emitting `retrieving`/`generating` phase events along the way.
    """

    def __init__(
        self,
        retriever: Optional[ProjectScopedRetriever] = None,
        generator: Optional[AnswerGenerator] = None,
        web_search_node: Optional[WebSearchNode] = None,
    ) -> None:
        self.retriever = retriever or ProjectScopedRetriever()
        self.generator = generator or AnswerGenerator()
        self.web_search_node = web_search_node or WebSearchNode()

    def ask(
        self,
        project_id: str,
        question: str,
        candidates: List[RetrievedChunk],
        settings: Optional[ConversationSettings] = None,
        on_phase: Optional[PhaseCallback] = None,
    ) -> AskResult:
        settings = settings or ConversationSettings(conversation_id="")

        if on_phase:
            on_phase("retrieving")

        document_candidates = _filter_by_document_type(
            candidates, settings.included_document_types
        )
        retrieved = self.retriever.retrieve(
            project_id, question, document_candidates, top_k=settings.retrieval_top_k
        )

        web_outcome = self.web_search_node.run(question, settings.web_search_enabled)
        retrieved = retrieved + web_outcome.chunks

        if on_phase:
            on_phase("generating")
        snippets = assemble_context(retrieved)

        try:
            generation = self.generator.generate(
                question, snippets, temperature=settings.temperature
            )
        except GenerationError as exc:
            return AskResult(
                content="",
                status=MessageStatus.FAILED,
                is_grounded=False,
                failure_reason=str(exc),
                used_web_search=web_outcome.attempted and not web_outcome.failed,
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
            used_web_search=web_outcome.attempted and not web_outcome.failed,
        )
