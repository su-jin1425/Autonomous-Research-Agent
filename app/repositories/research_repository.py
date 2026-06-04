from datetime import UTC, datetime

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.research import ExecutionMetric, ResearchQuery, ResearchReport, ResearchSource, ResearchTask
from app.monitoring.metrics import DATABASE_QUERY_DURATION


class ResearchRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_query(self, *, query: str, user_id: str | None = None) -> ResearchQuery:
        research = ResearchQuery(query=query, user_id=user_id, status="queued")
        self.session.add(research)
        with DATABASE_QUERY_DURATION.time():
            await self.session.flush()
        return research

    async def get_query(self, query_id: str) -> ResearchQuery | None:
        with DATABASE_QUERY_DURATION.time():
            result = await self.session.execute(
                select(ResearchQuery)
                .where(ResearchQuery.id == query_id)
                .options(
                    selectinload(ResearchQuery.sources),
                    selectinload(ResearchQuery.report),
                    selectinload(ResearchQuery.tasks),
                    selectinload(ResearchQuery.metrics),
                )
            )
        return result.scalar_one_or_none()

    async def list_queries(self, *, user_id: str | None = None, limit: int = 50) -> list[ResearchQuery]:
        statement = select(ResearchQuery).order_by(ResearchQuery.created_at.desc()).limit(limit)
        if user_id:
            statement = statement.where(ResearchQuery.user_id == user_id)
        with DATABASE_QUERY_DURATION.time():
            result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def delete_query(self, query_id: str, user_id: str | None = None) -> bool:
        statement = delete(ResearchQuery).where(ResearchQuery.id == query_id)
        if user_id:
            statement = statement.where(ResearchQuery.user_id == user_id)
        with DATABASE_QUERY_DURATION.time():
            result = await self.session.execute(statement)
        return bool(result.rowcount)

    async def update_status(self, query_id: str, status: str) -> None:
        with DATABASE_QUERY_DURATION.time():
            research = await self.session.get(ResearchQuery, query_id)
        if research is None:
            return
        research.status = status
        if status in {"completed", "failed", "cancelled"}:
            research.completed_at = datetime.now(UTC)
        with DATABASE_QUERY_DURATION.time():
            await self.session.flush()

    async def add_task(self, *, query_id: str, task_type: str, status: str, logs: dict | None = None) -> ResearchTask:
        task = ResearchTask(
            query_id=query_id,
            task_type=task_type,
            status=status,
            execution_logs=logs or {},
            started_at=datetime.now(UTC),
            completed_at=datetime.now(UTC) if status in {"completed", "failed"} else None,
        )
        self.session.add(task)
        with DATABASE_QUERY_DURATION.time():
            await self.session.flush()
        return task

    async def add_source(
        self,
        *,
        query_id: str,
        source_url: str,
        source_title: str | None,
        extracted_content: str,
        embedding_reference: str | None,
        quality_score: float,
    ) -> ResearchSource:
        source = ResearchSource(
            query_id=query_id,
            source_url=source_url,
            source_title=source_title,
            extracted_content=extracted_content,
            embedding_reference=embedding_reference,
            quality_score=quality_score,
        )
        self.session.add(source)
        with DATABASE_QUERY_DURATION.time():
            await self.session.flush()
        return source

    async def save_report(self, *, query_id: str, payload: dict, summary: str) -> ResearchReport:
        report = ResearchReport(query_id=query_id, report_payload=payload, generated_summary=summary)
        self.session.add(report)
        with DATABASE_QUERY_DURATION.time():
            await self.session.flush()
        return report

    async def get_report(self, report_id: str) -> ResearchReport | None:
        return await self.session.get(ResearchReport, report_id)

    async def save_metrics(
        self,
        *,
        query_id: str,
        execution_time: float,
        token_usage: int,
        retrieval_count: int,
    ) -> ExecutionMetric:
        metric = ExecutionMetric(
            query_id=query_id,
            execution_time=execution_time,
            token_usage=token_usage,
            retrieval_count=retrieval_count,
        )
        self.session.add(metric)
        with DATABASE_QUERY_DURATION.time():
            await self.session.flush()
        return metric

    async def count_by_status(self, status: str) -> int:
        with DATABASE_QUERY_DURATION.time():
            result = await self.session.execute(
                select(func.count()).select_from(ResearchQuery).where(ResearchQuery.status == status)
            )
        return int(result.scalar_one())
