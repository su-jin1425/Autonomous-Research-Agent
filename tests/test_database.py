from sqlalchemy import select

from app.models.research import (
    ExecutionMetric,
    ResearchQuery,
    ResearchReport,
    ResearchSource,
    ResearchTask,
)
from app.models.user import User
from app.repositories.research_repository import ResearchRepository
from app.repositories.user_repository import UserRepository


async def test_create_user(async_session):
    repository = UserRepository(async_session)

    user = await repository.create(
        name="Test User",
        email="test@example.com",
        password_hash="hashed-password",
        role="researcher",
    )

    await async_session.commit()

    assert user.id is not None
    assert user.email == "test@example.com"


async def test_get_user_by_email(async_session):
    repository = UserRepository(async_session)

    await repository.create(
        name="Test User",
        email="lookup@example.com",
        password_hash="hashed-password",
        role="researcher",
    )

    await async_session.commit()

    user = await repository.get_by_email(
        "lookup@example.com",
    )

    assert user is not None
    assert user.email == "lookup@example.com"


async def test_create_research_query(async_session):
    repository = ResearchRepository(async_session)

    query = await repository.create_query(
        query="Future of AI",
        user_id=None,
    )

    await async_session.commit()

    assert query.id is not None
    assert query.status == "queued"


async def test_get_research_query(async_session):
    repository = ResearchRepository(async_session)

    query = await repository.create_query(
        query="Vector Databases",
    )

    await async_session.commit()

    fetched = await repository.get_query(
        query.id,
    )

    assert fetched is not None
    assert fetched.query == "Vector Databases"


async def test_update_research_status(async_session):
    repository = ResearchRepository(async_session)

    query = await repository.create_query(
        query="LangGraph",
    )

    await repository.update_status(
        query.id,
        "completed",
    )

    await async_session.commit()

    fetched = await repository.get_query(
        query.id,
    )

    assert fetched.status == "completed"
    assert fetched.completed_at is not None


async def test_add_research_task(async_session):
    repository = ResearchRepository(async_session)

    query = await repository.create_query(
        query="Agent Systems",
    )

    task = await repository.add_task(
        query_id=query.id,
        task_type="workflow",
        status="running",
    )

    await async_session.commit()

    assert task.id is not None
    assert task.task_type == "workflow"


async def test_add_research_source(async_session):
    repository = ResearchRepository(async_session)

    query = await repository.create_query(
        query="FastAPI",
    )

    source = await repository.add_source(
        query_id=query.id,
        source_url="https://example.com",
        source_title="Example",
        extracted_content="Sample content",
        embedding_reference=None,
        quality_score=0.95,
    )

    await async_session.commit()

    assert source.id is not None
    assert source.source_url == "https://example.com"


async def test_save_report(async_session):
    repository = ResearchRepository(async_session)

    query = await repository.create_query(
        query="Redis",
    )

    report = await repository.save_report(
        query_id=query.id,
        payload={
            "summary": "Research Summary",
        },
        summary="Research Summary",
    )

    await async_session.commit()

    assert report.id is not None
    assert report.generated_summary == "Research Summary"


async def test_save_execution_metrics(async_session):
    repository = ResearchRepository(async_session)

    query = await repository.create_query(
        query="PostgreSQL",
    )

    metric = await repository.save_metrics(
        query_id=query.id,
        execution_time=1.25,
        token_usage=100,
        retrieval_count=5,
    )

    await async_session.commit()

    assert metric.execution_time == 1.25
    assert metric.token_usage == 100


async def test_count_by_status(async_session):
    repository = ResearchRepository(async_session)

    query = await repository.create_query(
        query="Monitoring",
    )

    await repository.update_status(
        query.id,
        "completed",
    )

    await async_session.commit()

    count = await repository.count_by_status(
        "completed",
    )

    assert count >= 1


async def test_delete_research_query(async_session):
    repository = ResearchRepository(async_session)

    query = await repository.create_query(
        query="Delete Me",
    )

    await async_session.commit()

    deleted = await repository.delete_query(
        query.id,
    )

    await async_session.commit()

    assert deleted is True


async def test_research_query_relationships(async_session):
    repository = ResearchRepository(async_session)

    query = await repository.create_query(
        query="Relationships Test",
    )

    await repository.add_source(
        query_id=query.id,
        source_url="https://example.com",
        source_title="Example",
        extracted_content="Content",
        embedding_reference=None,
        quality_score=0.9,
    )

    await repository.add_task(
        query_id=query.id,
        task_type="workflow",
        status="completed",
    )

    await repository.save_report(
        query_id=query.id,
        payload={"summary": "done"},
        summary="done",
    )

    await repository.save_metrics(
        query_id=query.id,
        execution_time=1.0,
        token_usage=10,
        retrieval_count=1,
    )

    await async_session.commit()

    fetched = await repository.get_query(
        query.id,
    )

    assert len(fetched.sources) == 1
    assert len(fetched.tasks) >= 1
    assert fetched.report is not None
    assert fetched.metrics is not None


async def test_user_research_relationship(async_session):
    user_repo = UserRepository(async_session)
    research_repo = ResearchRepository(async_session)

    user = await user_repo.create(
        name="Research Owner",
        email="owner@example.com",
        password_hash="hash",
        role="researcher",
    )

    query = await research_repo.create_query(
        query="Owned Query",
        user_id=user.id,
    )

    await async_session.commit()

    result = await async_session.execute(
        select(User).where(
            User.id == user.id,
        )
    )

    fetched_user = result.scalar_one()

    assert len(fetched_user.research_queries) == 1
    assert fetched_user.research_queries[0].id == query.id


async def test_execution_metric_model(async_session):
    query = ResearchQuery(
        query="Metric Test",
        status="completed",
    )

    async_session.add(query)
    await async_session.flush()

    metric = ExecutionMetric(
        query_id=query.id,
        execution_time=2.5,
        token_usage=500,
        retrieval_count=25,
    )

    async_session.add(metric)
    await async_session.commit()

    assert metric.execution_time == 2.5
    assert metric.retrieval_count == 25


async def test_report_model(async_session):
    query = ResearchQuery(
        query="Report Model Test",
    )

    async_session.add(query)
    await async_session.flush()

    report = ResearchReport(
        query_id=query.id,
        report_payload={
            "executive_summary": "summary",
        },
        generated_summary="summary",
    )

    async_session.add(report)
    await async_session.commit()

    assert report.generated_summary == "summary"


async def test_source_model(async_session):
    query = ResearchQuery(
        query="Source Model Test",
    )

    async_session.add(query)
    await async_session.flush()

    source = ResearchSource(
        query_id=query.id,
        source_url="https://example.com",
        source_title="Example",
        extracted_content="Example content",
        embedding_reference="ref",
        quality_score=0.99,
    )

    async_session.add(source)
    await async_session.commit()

    assert source.quality_score == 0.99


async def test_task_model(async_session):
    query = ResearchQuery(
        query="Task Model Test",
    )

    async_session.add(query)
    await async_session.flush()

    task = ResearchTask(
        query_id=query.id,
        task_type="workflow",
        status="completed",
    )

    async_session.add(task)
    await async_session.commit()

    assert task.status == "completed"