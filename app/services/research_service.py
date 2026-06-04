from time import perf_counter

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal
from app.models.research import ResearchQuery
from app.monitoring.metrics import RESEARCH_LATENCY, RESEARCH_RUNS, RETRIEVAL_COUNT
from app.repositories.research_repository import ResearchRepository
from app.schemas.research import ResearchStartRequest
from app.services.redis_service import RedisService
from app.workflows.research_graph import ResearchWorkflow


class ResearchNotFoundError(ValueError):
    pass


class ResearchService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repository = ResearchRepository(session)

    async def start(self, *, request: ResearchStartRequest, user_id: str | None) -> ResearchQuery:
        research = await self.repository.create_query(query=request.query, user_id=user_id)
        await self.session.commit()
        return research

    async def list(self, *, user_id: str | None = None) -> list[ResearchQuery]:
        return await self.repository.list_queries(user_id=user_id)

    async def get(self, *, query_id: str, user_id: str | None = None) -> ResearchQuery:
        research = await self.repository.get_query(query_id)
        if research is None or (user_id and research.user_id != user_id):
            raise ResearchNotFoundError("Research query not found")
        return research

    async def delete(self, *, query_id: str, user_id: str | None = None) -> None:
        deleted = await self.repository.delete_query(query_id, user_id=user_id)
        await self.session.commit()
        if not deleted:
            raise ResearchNotFoundError("Research query not found")


async def execute_research_job(query_id: str, *, max_sources: int, max_depth: int) -> None:
    redis = RedisService()
    async with AsyncSessionLocal() as session:
        repository = ResearchRepository(session)
        start_time = perf_counter()
        await repository.update_status(query_id, "running")
        await repository.add_task(query_id=query_id, task_type="workflow", status="running")
        await session.commit()
        await redis.publish_execution_update(query_id, {"status": "running"})

        research = await repository.get_query(query_id)
        if research is None:
            return

        try:
            workflow = ResearchWorkflow()
            with RESEARCH_LATENCY.time():
                state = await workflow.run(query=research.query, max_sources=max_sources, max_depth=max_depth)

            documents = state.get("browsed_documents", [])
            for document in documents:
                await repository.add_source(
                    query_id=query_id,
                    source_url=document.url,
                    source_title=document.title,
                    extracted_content=document.content[:20000],
                    embedding_reference=None,
                    quality_score=document.score,
                )
            report = state.get("report", {})
            await repository.save_report(
                query_id=query_id,
                payload=report,
                summary=str(report.get("executive_summary", "")),
            )
            await repository.save_metrics(
                query_id=query_id,
                execution_time=perf_counter() - start_time,
                token_usage=0,
                retrieval_count=len(documents),
            )
            await repository.add_task(query_id=query_id, task_type="workflow", status="completed", logs=report)
            await repository.update_status(query_id, "completed")
            await session.commit()
            RESEARCH_RUNS.labels(status="completed").inc()
            RETRIEVAL_COUNT.inc(len(documents))
            await redis.publish_execution_update(query_id, {"status": "completed"})
        except Exception as exc:
            await repository.add_task(query_id=query_id, task_type="workflow", status="failed", logs={"error": str(exc)})
            await repository.update_status(query_id, "failed")
            await session.commit()
            RESEARCH_RUNS.labels(status="failed").inc()
            await redis.publish_execution_update(query_id, {"status": "failed", "error": str(exc)})

