from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class VectorizedChunk:
    chunk_id: str
    embedding: List[float]
    metadata: Dict[str, Any]


class Vectorizer:
    def vectorize(self, chunk_id: str, metadata: Dict[str, Any]) -> VectorizedChunk:
        return VectorizedChunk(
            chunk_id=chunk_id,
            embedding=[0.0, 0.0, 1.0],
            metadata=metadata,
        )
