from dataclasses import dataclass
from math import sqrt
from typing import Protocol

from app.retrieval.documents import DocumentChunk


@dataclass(slots=True)
class VectorHit:
    id: str
    text: str
    metadata: dict[str, str | int | float]
    score: float


class VectorStore(Protocol):
    async def add(self, chunks: list[DocumentChunk], embeddings: list[list[float]]) -> list[str]: ...

    async def search(self, query_embedding: list[float], limit: int = 5) -> list[VectorHit]: ...


class InMemoryVectorStore:
    def __init__(self) -> None:
        self._items: list[tuple[DocumentChunk, list[float]]] = []

    async def add(self, chunks: list[DocumentChunk], embeddings: list[list[float]]) -> list[str]:
        self._items.extend(zip(chunks, embeddings, strict=True))
        return [chunk.id for chunk in chunks]

    async def search(self, query_embedding: list[float], limit: int = 5) -> list[VectorHit]:
        scored: list[VectorHit] = []
        for chunk, embedding in self._items:
            scored.append(
                VectorHit(
                    id=chunk.id,
                    text=chunk.text,
                    metadata=chunk.metadata,
                    score=_cosine_similarity(query_embedding, embedding),
                )
            )
        return sorted(scored, key=lambda hit: hit.score, reverse=True)[:limit]


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right, strict=False))
    left_norm = sqrt(sum(a * a for a in left)) or 1.0
    right_norm = sqrt(sum(b * b for b in right)) or 1.0
    return dot / (left_norm * right_norm)
