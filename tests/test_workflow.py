import pytest

from app.retrieval.documents import RetrievedDocument
from app.services.knowledge_base import KnowledgeBaseService
from app.vectorstore.base import InMemoryVectorStore
from app.vectorstore.embeddings import EmbeddingProvider
from app.workflows.research_graph import ResearchWorkflow


class FakeSearchClient:
    async def search(self, query: str, limit: int = 5) -> list[RetrievedDocument]:
        return [
            RetrievedDocument(
                url=f"https://example.com/{query.replace(' ', '-')}",
                title=f"Result for {query}",
                content="FastAPI LangGraph Redis PostgreSQL vector search research automation evidence.",
                score=0.9,
            )
        ]


class FakeBrowser:
    async def fetch(self, url: str) -> RetrievedDocument:
        return RetrievedDocument(
            url=url,
            title="Fetched page",
            content=" ".join(["FastAPI LangGraph Redis PostgreSQL vector search research automation evidence"] * 80),
            score=0.9,
        )


@pytest.mark.asyncio
async def test_research_workflow_generates_validated_report() -> None:
    workflow = ResearchWorkflow(
        search_client=FakeSearchClient(),
        browser=FakeBrowser(),
        knowledge_base=KnowledgeBaseService(vector_store=InMemoryVectorStore(), embeddings=EmbeddingProvider()),
    )

    state = await workflow.run(query="autonomous research agent architecture", max_sources=2, max_depth=1)

    assert state["indexed_chunk_ids"]
    assert state["report"]["executive_summary"]
    assert state["report"]["validation"]["citation_count"] >= 1

