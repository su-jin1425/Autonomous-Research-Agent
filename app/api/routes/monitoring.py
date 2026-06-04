from fastapi import APIRouter, Depends
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from app.api.deps import db_session, require_roles
from app.core.config import get_settings
from app.models.user import User
from app.repositories.research_repository import ResearchRepository
from app.schemas.monitoring import HealthResponse, MetricsResponse
from app.services.redis_service import RedisService


router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/health", response_model=HealthResponse)
async def health(session: AsyncSession = Depends(db_session)) -> HealthResponse:
    settings = get_settings()
    database = "ok"
    redis_status = "ok"
    try:
        await session.execute(text("SELECT 1"))
    except Exception:
        database = "error"
    try:
        await RedisService().ping()
    except Exception:
        redis_status = "error"
    status = "ok" if database == "ok" and redis_status == "ok" else "degraded"
    return HealthResponse(status=status, environment=settings.environment, database=database, redis=redis_status)


@router.get("/metrics")
async def prometheus_metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@router.get("/executions", response_model=MetricsResponse)
async def execution_metrics(
    session: AsyncSession = Depends(db_session),
    _: User = Depends(require_roles("admin", "analyst")),
) -> MetricsResponse:
    repository = ResearchRepository(session)
    return MetricsResponse(
        queued_research=await repository.count_by_status("queued"),
        running_research=await repository.count_by_status("running"),
        completed_research=await repository.count_by_status("completed"),
        failed_research=await repository.count_by_status("failed"),
    )
