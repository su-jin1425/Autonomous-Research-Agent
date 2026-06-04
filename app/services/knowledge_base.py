from app.retrieval.chunking import TextChunker
from app.retrieval.documents import RetrievedDocument
from app.vectorstore.base import VectorHit, VectorStore
from app.vectorstore.chroma_store import ChromaVectorStore
from app.vectorstore.embeddings import EmbeddingProvider


class KnowledgeBaseService:
    def __init__(self, vector_store: VectorStore | None = None, embeddings: EmbeddingProvider | None = None) -> None:
        self.vector_store = vector_store or ChromaVectorStore()
        self.embeddings = embeddings or EmbeddingProvider()
        self.chunker = TextChunker()

    async def index_documents(self, documents: list[RetrievedDocument]) -> list[str]:
        chunks = []
        for document in documents:
            chunks.extend(self.chunker.chunk(document))
        if not chunks:
            return []
        vectors = self.embeddings.embed([chunk.text for chunk in chunks])
        return await self.vector_store.add(chunks, vectors)

    async def semantic_search(self, query: str, limit: int = 5) -> list[VectorHit]:
        query_embedding = self.embeddings.embed([query])[0]
        return await self.vector_store.search(query_embedding, limit=limit)

