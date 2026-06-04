from app.core.config import get_settings
from app.retrieval.documents import DocumentChunk
from app.vectorstore.base import InMemoryVectorStore, VectorHit, VectorStore


class ChromaVectorStore:
    def __init__(self, collection_name: str = "research_chunks") -> None:
        self.settings = get_settings()
        try:
            import chromadb
        except ImportError:
            self._fallback: VectorStore | None = InMemoryVectorStore()
            self._collection = None
            return

        self._fallback = None
        client = chromadb.PersistentClient(path=self.settings.chroma_persist_dir)
        self._collection = client.get_or_create_collection(collection_name)

    async def add(self, chunks: list[DocumentChunk], embeddings: list[list[float]]) -> list[str]:
        if self._fallback:
            return await self._fallback.add(chunks, embeddings)
        if not chunks:
            return []
        assert self._collection is not None
        self._collection.upsert(
            ids=[chunk.id for chunk in chunks],
            documents=[chunk.text for chunk in chunks],
            embeddings=embeddings,
            metadatas=[chunk.metadata for chunk in chunks],
        )
        return [chunk.id for chunk in chunks]

    async def search(self, query_embedding: list[float], limit: int = 5) -> list[VectorHit]:
        if self._fallback:
            return await self._fallback.search(query_embedding, limit)
        assert self._collection is not None
        result = self._collection.query(query_embeddings=[query_embedding], n_results=limit)
        hits: list[VectorHit] = []
        for index, item_id in enumerate(result.get("ids", [[]])[0]):
            distance = result.get("distances", [[1.0]])[0][index]
            hits.append(
                VectorHit(
                    id=item_id,
                    text=result.get("documents", [[""]])[0][index],
                    metadata=result.get("metadatas", [[{}]])[0][index] or {},
                    score=1.0 - float(distance),
                )
            )
        return hits

