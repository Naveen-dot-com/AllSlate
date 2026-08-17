from __future__ import annotations

from typing import Dict, List, Optional

from backend.app.models.document import ProcessedElement
from backend.app.models.message import MessageCitation
from backend.app.rag.retriever import RetrievedChunk


def build_citations(
    contributing_chunks: List[RetrievedChunk],
    asset_urls: Optional[Dict[str, str]] = None,
) -> List[MessageCitation]:
    """Map contributing chunks to persisted citation rows.

    When a contributing chunk's metadata includes an `asset_reference_id`,
    resolve it to a Storage URL (via `asset_urls`) so the original table/image
    is attached alongside its summary text (FR-006-FR-008).
    """
    asset_urls = asset_urls or {}
    citations: List[MessageCitation] = []
    seen_chunk_ids: set[str] = set()

    for chunk in contributing_chunks:
        if chunk.chunk_id in seen_chunk_ids:
            continue
        seen_chunk_ids.add(chunk.chunk_id)
        citations.append(
            MessageCitation(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                asset_reference_id=chunk.asset_reference_id,
                page_number=chunk.page_number,
                asset_reference_url=(
                    asset_urls.get(chunk.asset_reference_id)
                    if chunk.asset_reference_id
                    else None
                ),
            )
        )
    return citations


def resolve_citation_confidence(
    chunk: RetrievedChunk,
    elements_by_id: Dict[str, ProcessedElement],
) -> tuple[str, Optional[str]] | None:
    """T040: read-only lookup of a citation's source-element confidence.

    Reads `elements.confidence`/`confidence_reason` via the existing
    `chunks.element_id` relationship (carried in `chunk.metadata["element_id"]`), for
    future use surfacing confidence on chat citations (FR-015). No new schema required.
    """
    element_id = chunk.metadata.get("element_id")
    if not element_id:
        return None
    element = elements_by_id.get(element_id)
    if element is None:
        return None
    return (element.confidence, element.confidence_reason)

