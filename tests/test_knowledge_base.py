import pytest

from app.retrieval.documents import RetrievedDocument
from app.services.knowledge_base import KnowledgeBaseService
from app.vectorstore.base import InMemoryVectorStore


class FakeEmbeddingProvider:
    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            lowered = text.lower()
            if "fastapi" in lowered:
                vectors.append([1.0, 0.0, 0.0])
            elif "redis" in lowered:
                vectors.append([0.0, 1.0, 0.0])
            else:
                vectors.append([0.0, 0.0, 1.0])
        return vectors


@pytest.mark.asyncio
async def test_knowledge_base_indexes_and_searches_documents() -> None:
    service = KnowledgeBaseService(
        vector_store=InMemoryVectorStore(),
        embeddings=FakeEmbeddingProvider(),
    )

    documents = [
        RetrievedDocument(
            url="https://example.com/fastapi",
            title="FastAPI Guide",
            content="FastAPI research platform architecture and API design",
            score=0.9,
        ),
        RetrievedDocument(
            url="https://example.com/redis",
            title="Redis Guide",
            content="Redis queue orchestration and caching patterns",
            score=0.7,
        ),
    ]

    chunk_ids = await service.index_documents(documents)
    hits = await service.semantic_search("fastapi architecture", limit=1)

    assert chunk_ids
    assert hits[0].metadata["url"] == "https://example.com/fastapi"


@pytest.mark.asyncio
async def test_knowledge_base_handles_empty_documents() -> None:
    service = KnowledgeBaseService(
        vector_store=InMemoryVectorStore(),
        embeddings=FakeEmbeddingProvider(),
    )

    chunk_ids = await service.index_documents([])

    assert chunk_ids == []
