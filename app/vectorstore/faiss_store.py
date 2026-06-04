import json
from pathlib import Path

from app.core.config import get_settings
from app.retrieval.documents import DocumentChunk
from app.vectorstore.base import InMemoryVectorStore, VectorHit, VectorStore


class FaissVectorStore:
    def __init__(self) -> None:
        self.settings = get_settings()
        try:
            import faiss
            import numpy as np
        except ImportError:
            self._fallback: VectorStore | None = InMemoryVectorStore()
            self._faiss = None
            self._np = None
            self._index = None
            self._chunks: list[DocumentChunk] = []
            return

        self._fallback = None
        self._faiss = faiss
        self._np = np
        self._index = None
        self._chunks: list[DocumentChunk] = []

    async def add(self, chunks: list[DocumentChunk], embeddings: list[list[float]]) -> list[str]:
        if self._fallback:
            return await self._fallback.add(chunks, embeddings)
        if not embeddings:
            return []
        assert self._faiss is not None and self._np is not None
        matrix = self._np.array(embeddings, dtype="float32")
        if self._index is None:
            self._index = self._faiss.IndexFlatIP(matrix.shape[1])
        self._index.add(matrix)
        self._chunks.extend(chunks)
        self._persist_metadata()
        return [chunk.id for chunk in chunks]

    async def search(self, query_embedding: list[float], limit: int = 5) -> list[VectorHit]:
        if self._fallback:
            return await self._fallback.search(query_embedding, limit)
        if self._index is None or not self._chunks:
            return []
        assert self._np is not None
        scores, indexes = self._index.search(self._np.array([query_embedding], dtype="float32"), limit)
        hits: list[VectorHit] = []
        for score, index in zip(scores[0], indexes[0], strict=False):
            if index < 0:
                continue
            chunk = self._chunks[int(index)]
            hits.append(VectorHit(id=chunk.id, text=chunk.text, metadata=chunk.metadata, score=float(score)))
        return hits

    def _persist_metadata(self) -> None:
        path = Path(self.settings.faiss_index_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if self._faiss is not None and self._index is not None:
            self._faiss.write_index(self._index, str(path))
        metadata_path = path.with_suffix(".metadata.json")
        metadata_path.write_text(
            json.dumps([{"id": chunk.id, "text": chunk.text, "metadata": chunk.metadata} for chunk in self._chunks]),
            encoding="utf-8",
        )
