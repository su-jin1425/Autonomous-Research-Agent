import argparse
import asyncio
import json
from pathlib import Path
from time import perf_counter

from app.retrieval.documents import RetrievedDocument
from app.services.knowledge_base import KnowledgeBaseService


FIXTURES = [
    RetrievedDocument(
        url="https://example.com/fastapi",
        title="FastAPI research APIs",
        content="FastAPI async APIs structured validation OpenAPI research orchestration " * 120,
        score=0.9,
    ),
    RetrievedDocument(
        url="https://example.com/vector",
        title="Vector search",
        content="Vector database embeddings semantic retrieval FAISS Chroma optimization " * 120,
        score=0.9,
    ),
    RetrievedDocument(
        url="https://example.com/browser",
        title="Browser automation",
        content="Playwright autonomous navigation extraction dynamic website handling " * 120,
        score=0.9,
    ),
]


async def run(iterations: int) -> dict:
    kb = KnowledgeBaseService()
    start = perf_counter()
    indexed = await kb.index_documents(FIXTURES)
    indexing_seconds = perf_counter() - start

    search_latencies = []
    for _ in range(iterations):
        query_start = perf_counter()
        await kb.semantic_search("FastAPI vector retrieval automation", limit=3)
        search_latencies.append(perf_counter() - query_start)

    return {
        "indexed_chunks": len(indexed),
        "indexing_seconds": indexing_seconds,
        "search_iterations": iterations,
        "average_search_seconds": sum(search_latencies) / len(search_latencies),
        "min_search_seconds": min(search_latencies),
        "max_search_seconds": max(search_latencies),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=20)
    parser.add_argument("--output", type=Path, default=Path("benchmark-results/retrieval.json"))
    args = parser.parse_args()

    result = asyncio.run(run(args.iterations))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

