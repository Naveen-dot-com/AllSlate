from __future__ import annotations

from typing import Dict, List, Optional

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
