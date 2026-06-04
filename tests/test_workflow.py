import pytest

from app.retrieval.browser import BrowserNavigationError
from app.retrieval.documents import RetrievedDocument
from app.services.knowledge_base import KnowledgeBaseService
from app.vectorstore.base import InMemoryVectorStore
from app.vectorstore.embeddings import EmbeddingProvider
from app.workflows.research_graph import ResearchWorkflow


class FakeSearchClient:
    async def search(
        self,
        query: str,
        limit: int = 5,
    ) -> list[RetrievedDocument]:
        return [
            RetrievedDocument(
                url=f"https://example.com/{query.replace(' ', '-')}",
                title=f"Result for {query}",
                content=(
                    "FastAPI LangGraph Redis PostgreSQL "
                    "vector search research automation evidence."
                ),
                score=0.9,
            )
        ]


class EmptySearchClient:
    async def search(
        self,
        query: str,
        limit: int = 5,
    ) -> list[RetrievedDocument]:
        return []


class FailingSearchClient:
    async def search(
        self,
        query: str,
        limit: int = 5,
    ) -> list[RetrievedDocument]:
        raise RuntimeError("search failure")


class FakeBrowser:
    async def fetch(
        self,
        url: str,
    ) -> RetrievedDocument:
        return RetrievedDocument(
            url=url,
            title="Fetched page",
            content=" ".join(
                [
                    "FastAPI LangGraph Redis PostgreSQL vector search "
                    "research automation evidence"
                ]
                * 80
            ),
            score=0.9,
        )


class FailingBrowser:
    async def fetch(
        self,
        url: str,
    ) -> RetrievedDocument:
        raise BrowserNavigationError(
            "navigation failed"
        )


@pytest.mark.asyncio
async def test_research_workflow_generates_validated_report():
    workflow = ResearchWorkflow(
        search_client=FakeSearchClient(),
        browser=FakeBrowser(),
        knowledge_base=KnowledgeBaseService(
            vector_store=InMemoryVectorStore(),
            embeddings=EmbeddingProvider(),
        ),
    )

    state = await workflow.run(
        query="autonomous research agent architecture",
        max_sources=2,
        max_depth=1,
    )

    assert state["indexed_chunk_ids"]
    assert state["report"]["executive_summary"]
    assert (
        state["report"]["validation"]["citation_count"]
        >= 1
    )


@pytest.mark.asyncio
async def test_workflow_handles_empty_results():
    workflow = ResearchWorkflow(
        search_client=EmptySearchClient(),
        browser=FakeBrowser(),
        knowledge_base=KnowledgeBaseService(
            vector_store=InMemoryVectorStore(),
            embeddings=EmbeddingProvider(),
        ),
    )

    state = await workflow.run(
        query="nonexistent query",
    )

    assert "report" in state


@pytest.mark.asyncio
async def test_workflow_handles_search_failure():
    workflow = ResearchWorkflow(
        search_client=FailingSearchClient(),
        browser=FakeBrowser(),
        knowledge_base=KnowledgeBaseService(
            vector_store=InMemoryVectorStore(),
            embeddings=EmbeddingProvider(),
        ),
    )

    state = await workflow.run(
        query="failure case",
    )

    assert state["errors"]


@pytest.mark.asyncio
async def test_workflow_handles_browser_failure():
    workflow = ResearchWorkflow(
        search_client=FakeSearchClient(),
        browser=FailingBrowser(),
        knowledge_base=KnowledgeBaseService(
            vector_store=InMemoryVectorStore(),
            embeddings=EmbeddingProvider(),
        ),
    )

    state = await workflow.run(
        query="browser failure",
    )

    assert state["errors"]


@pytest.mark.asyncio
async def test_report_contains_validation_block():
    workflow = ResearchWorkflow(
        search_client=FakeSearchClient(),
        browser=FakeBrowser(),
        knowledge_base=KnowledgeBaseService(
            vector_store=InMemoryVectorStore(),
            embeddings=EmbeddingProvider(),
        ),
    )

    state = await workflow.run(
        query="validation test",
    )

    validation = state["report"]["validation"]

    assert "citation_count" in validation
    assert "source_count" in validation
    assert "status" in validation