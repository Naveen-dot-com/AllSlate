from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from backend.app.rag.retriever import RetrievedChunk

WebSearchCall = Callable[[str], List[RetrievedChunk]]


@dataclass
class WebSearchOutcome:
    chunks: List[RetrievedChunk] = field(default_factory=list)
    attempted: bool = False
    failed: bool = False


class WebSearchNode:
    """Conditional LangGraph-style node: supplements context with web results.

    Runs only when `web_search_enabled` is true. On any failure/timeout, it
    fails open — falling back to document-only context — rather than failing
    the whole answer (constitution Principle VII; research.md #3).
    """

    def __init__(self, search_call: Optional[WebSearchCall] = None, max_results: int = 3) -> None:
        self._search_call = search_call
        self.max_results = max_results

    def run(self, question: str, web_search_enabled: bool) -> WebSearchOutcome:
        if not web_search_enabled:
            return WebSearchOutcome(chunks=[], attempted=False, failed=False)

        if self._search_call is None:
            # No web search client configured: treat as a graceful no-op, not a hard failure.
            return WebSearchOutcome(chunks=[], attempted=True, failed=True)

        try:
            results = self._search_call(question)
        except Exception:  # noqa: BLE001 - any web-search failure must fail open
            return WebSearchOutcome(chunks=[], attempted=True, failed=True)

        for chunk in results:
            chunk.element_type = "web"
        return WebSearchOutcome(chunks=results[: self.max_results], attempted=True, failed=False)
