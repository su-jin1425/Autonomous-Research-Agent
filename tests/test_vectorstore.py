import pytest

from app.retrieval.documents import DocumentChunk
from app.vectorstore.base import InMemoryVectorStore
from app.vectorstore.embeddings import EmbeddingProvider


@pytest.mark.asyncio
async def test_in_memory_vector_store_returns_semantic_hit() -> None:
    embeddings = EmbeddingProvider()
    store = InMemoryVectorStore()
    chunks = [
        DocumentChunk(id="a", text="postgres redis fastapi orchestration", metadata={"url": "a"}),
        DocumentChunk(id="b", text="gardening soil compost", metadata={"url": "b"}),
    ]
    await store.add(chunks, embeddings.embed([chunk.text for chunk in chunks]))

    hits = await store.search(embeddings.embed(["fastapi redis research"])[0], limit=1)

    assert hits[0].id == "a"
