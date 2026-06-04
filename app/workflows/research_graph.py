from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable

from app.agents.planner import ResearchPlanner
from app.agents.reasoning import ReasoningAgent
from app.core.config import get_settings
from app.retrieval.browser import BrowserNavigationError, PlaywrightBrowser
from app.retrieval.documents import RetrievedDocument
from app.retrieval.search import WebSearchClient
from app.services.knowledge_base import KnowledgeBaseService
from app.services.source_validation import SourceValidator
from app.workflows.state import ResearchState


logger = logging.getLogger(__name__)

GraphNode = Callable[[ResearchState], Awaitable[ResearchState]]


class ResearchWorkflow:
    def __init__(
        self,
        search_client: WebSearchClient | None = None,
        browser: PlaywrightBrowser | None = None,
        knowledge_base: KnowledgeBaseService | None = None,
        reasoning_agent: ReasoningAgent | None = None,
        planner: ResearchPlanner | None = None,
    ) -> None:
        self.settings = get_settings()

        self.search_client = search_client or WebSearchClient()
        self.browser = browser or PlaywrightBrowser()
        self.knowledge_base = knowledge_base or KnowledgeBaseService()
        self.reasoning_agent = reasoning_agent or ReasoningAgent()
        self.planner = planner or ResearchPlanner()

        self.validator = SourceValidator()

        self._compiled_graph = self._build_langgraph()

    async def run(
        self,
        *,
        query: str,
        max_sources: int | None = None,
        max_depth: int | None = None,
    ) -> ResearchState:
        state: ResearchState = {
            "query": query,
            "max_sources": max_sources or self.settings.research_max_sources,
            "max_depth": max_depth or self.settings.research_max_depth,
            "errors": [],
            "research_iterations": 0,
            "confidence_score": 0.0,
            "knowledge_gaps": [],
        }

        if self._compiled_graph is not None:
            return await self._compiled_graph.ainvoke(state)

        return await self._run_sequential(state)

    def _build_langgraph(self):
        try:
            from langgraph.graph import END, StateGraph
        except ImportError:
            return None

        graph = StateGraph(ResearchState)

        graph.add_node("plan", self.plan_research)
        graph.add_node("search", self.search_web)
        graph.add_node("browse", self.browse_sources)
        graph.add_node("index", self.index_documents)
        graph.add_node("evaluate", self.evaluate_evidence)
        graph.add_node("reason", self.reason_over_evidence)
        graph.add_node("validate", self.validate_report)

        graph.set_entry_point("plan")

        graph.add_edge("plan", "search")
        graph.add_edge("search", "browse")
        graph.add_edge("browse", "index")
        graph.add_edge("index", "evaluate")
        graph.add_edge("evaluate", "reason")
        graph.add_edge("reason", "validate")
        graph.add_edge("validate", END)

        return graph.compile()

    async def _run_sequential(
        self,
        state: ResearchState,
    ) -> ResearchState:
        for node in [
            self.plan_research,
            self.search_web,
            self.browse_sources,
            self.index_documents,
            self.evaluate_evidence,
            self.reason_over_evidence,
            self.validate_report,
        ]:
            state = await node(state)

        return state

    async def plan_research(
        self,
        state: ResearchState,
    ) -> ResearchState:
        plan = await self.planner.create_plan(
            query=state["query"],
            max_depth=state["max_depth"],
        )

        state["research_plan"] = plan
        state["sub_questions"] = plan.get(
            "sub_questions",
            [],
        )
        state["search_tasks"] = plan.get(
            "search_tasks",
            [],
        )

        return state

    async def search_web(
        self,
        state: ResearchState,
    ) -> ResearchState:
        search_tasks = state.get(
            "search_tasks",
            [],
        )

        if not search_tasks:
            return state

        limit_per_task = max(
            1,
            state["max_sources"] // max(
                1,
                len(search_tasks),
            ),
        )

        batches = await asyncio.gather(
            *(
                self.search_client.search(
                    task,
                    limit=limit_per_task,
                )
                for task in search_tasks
            ),
            return_exceptions=True,
        )

        results: list[RetrievedDocument] = []
        seen_urls: set[str] = set()

        for batch in batches:
            if isinstance(batch, Exception):
                state.setdefault(
                    "errors",
                    [],
                ).append(str(batch))
                continue

            for document in batch:
                if document.url in seen_urls:
                    continue

                seen_urls.add(document.url)
                results.append(document)

        state["search_results"] = results[
            : state["max_sources"]
        ]

        return state

    async def browse_sources(
        self,
        state: ResearchState,
    ) -> ResearchState:
        documents: list[RetrievedDocument] = []

        for result in state.get(
            "search_results",
            [],
        ):
            try:
                page = await self.browser.fetch(
                    result.url,
                )

                page.score = result.score

                page.metadata.update(
                    result.metadata,
                )

                documents.append(page)

            except BrowserNavigationError as exc:
                state.setdefault(
                    "errors",
                    [],
                ).append(str(exc))

                documents.append(result)

            except Exception as exc:
                logger.exception(
                    "Unexpected browse failure",
                    extra={
                        "url": result.url,
                    },
                )

                state.setdefault(
                    "errors",
                    [],
                ).append(
                    f"{result.url}: {exc}"
                )

                documents.append(result)

        for document in documents:
            document.score = self.validator.score(
                document
            )

        state["browsed_documents"] = sorted(
            documents,
            key=lambda doc: doc.score,
            reverse=True,
        )

        return state

    async def index_documents(
        self,
        state: ResearchState,
    ) -> ResearchState:
        documents = state.get(
            "browsed_documents",
            [],
        )

        state["indexed_chunk_ids"] = (
            await self.knowledge_base.index_documents(
                documents
            )
        )

        state["evidence"] = (
            await self.knowledge_base.semantic_search(
                state["query"],
                limit=8,
            )
        )

        return state

    async def evaluate_evidence(
        self,
        state: ResearchState,
    ) -> ResearchState:
        evidence = state.get(
            "evidence",
            [],
        )

        confidence = min(
            len(evidence) / 8.0,
            1.0,
        )

        state["confidence_score"] = round(
            confidence,
            4,
        )

        knowledge_gaps: list[str] = []

        if len(evidence) < 3:
            knowledge_gaps.append(
                "Insufficient supporting evidence"
            )

        if not evidence:
            knowledge_gaps.append(
                "No semantically relevant evidence found"
            )

        state["knowledge_gaps"] = knowledge_gaps

        state["research_iterations"] = (
            state.get(
                "research_iterations",
                0,
            )
            + 1
        )

        return state

    async def reason_over_evidence(
        self,
        state: ResearchState,
    ) -> ResearchState:
        state["report"] = (
            await self.reasoning_agent.synthesize(
                query=state["query"],
                evidence=state.get(
                    "evidence",
                    [],
                ),
            )
        )

        return state

    async def validate_report(
        self,
        state: ResearchState,
    ) -> ResearchState:
        report = state.get(
            "report",
            {},
        )

        citations = report.get(
            "citations",
            [],
        )

        report["validation"] = {
            "citation_count": len(
                citations
            ),
            "source_count": len(
                state.get(
                    "browsed_documents",
                    [],
                )
            ),
            "indexed_chunks": len(
                state.get(
                    "indexed_chunk_ids",
                    [],
                )
            ),
            "confidence_score": state.get(
                "confidence_score",
                0.0,
            ),
            "knowledge_gaps": state.get(
                "knowledge_gaps",
                [],
            ),
            "research_iterations": state.get(
                "research_iterations",
                0,
            ),
            "errors": state.get(
                "errors",
                [],
            ),
            "status": (
                "needs_review"
                if (
                    not citations
                    or state.get("errors")
                )
                else "validated_with_sources"
            ),
        }

        state["report"] = report

        return state