from typing import TypedDict

from app.retrieval.documents import RetrievedDocument
from app.vectorstore.base import VectorHit


class ResearchState(TypedDict, total=False):
    query: str

    max_sources: int
    max_depth: int

    research_plan: dict

    sub_questions: list[str]

    search_tasks: list[str]

    search_results: list[RetrievedDocument]

    browsed_documents: list[RetrievedDocument]

    indexed_chunk_ids: list[str]

    evidence: list[VectorHit]

    knowledge_gaps: list[str]

    confidence_score: float

    research_iterations: int

    report: dict

    errors: list[str]