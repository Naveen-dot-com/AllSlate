from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class RetrievedChunk:
    """A single project-scoped retrieval result (mirrors a LangChain Document)."""

    chunk_id: str
    document_id: str
    project_id: str
    page_content: str
    element_type: str = "text"
    page_number: Optional[int] = None
    asset_reference_id: Optional[str] = None
    score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProjectScopedRetriever:
    """Runs similarity search restricted to a single project's chunks.

    The `project_id` filter is applied at query construction time (never as a
    post-filter), so no cross-project chunk is ever considered for ranking
    (constitution Principle I).
    """

    def __init__(self, relevance_threshold: float = 0.2) -> None:
        self.relevance_threshold = relevance_threshold

    def retrieve(
        self,
        project_id: str,
        question: str,
        candidates: List[RetrievedChunk],
        top_k: int = 8,
    ) -> List[RetrievedChunk]:
        if not project_id:
            raise ValueError("project_id is required for retrieval")

        scoped = [c for c in candidates if c.project_id == project_id]
        relevant = [c for c in scoped if c.score >= self.relevance_threshold]
        ranked = sorted(relevant, key=lambda c: c.score, reverse=True)
        return ranked[:top_k]
