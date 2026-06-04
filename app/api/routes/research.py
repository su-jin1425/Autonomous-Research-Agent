from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session, get_current_user
from app.core.config import get_settings
from app.models.user import User
from app.schemas.research import ResearchDetailResponse, ResearchQueryResponse, ResearchStartRequest
from app.services.research_service import ResearchNotFoundError, ResearchService, execute_research_job
from app.tasks import run_research


router = APIRouter(prefix="/research", tags=["research"])


@router.post("/start", response_model=ResearchQueryResponse, status_code=status.HTTP_202_ACCEPTED)
async def start_research(
    request: ResearchStartRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(db_session),
    user: User = Depends(get_current_user),
) -> ResearchQueryResponse:
    research = await ResearchService(session).start(request=request, user_id=user.id)
    settings = get_settings()
    if request.async_execution:
        if settings.use_celery:
            run_research.delay(research.id, request.max_sources, request.max_depth)
        else:
            background_tasks.add_task(
                execute_research_job,
                research.id,
                max_sources=request.max_sources,
                max_depth=request.max_depth,
            )
    else:
        await execute_research_job(research.id, max_sources=request.max_sources, max_depth=request.max_depth)
    return ResearchQueryResponse.model_validate(research)


@router.get("", response_model=list[ResearchQueryResponse])
async def list_research(
    session: AsyncSession = Depends(db_session),
    user: User = Depends(get_current_user),
) -> list[ResearchQueryResponse]:
    queries = await ResearchService(session).list(user_id=user.id)
    return [ResearchQueryResponse.model_validate(query) for query in queries]


@router.get("/status/{query_id}", response_model=ResearchQueryResponse)
async def research_status(
    query_id: str,
    session: AsyncSession = Depends(db_session),
    user: User = Depends(get_current_user),
) -> ResearchQueryResponse:
    try:
        query = await ResearchService(session).get(query_id=query_id, user_id=user.id)
    except ResearchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ResearchQueryResponse.model_validate(query)


@router.get("/{query_id}", response_model=ResearchDetailResponse)
async def research_detail(
    query_id: str,
    session: AsyncSession = Depends(db_session),
    user: User = Depends(get_current_user),
) -> ResearchDetailResponse:
    try:
        query = await ResearchService(session).get(query_id=query_id, user_id=user.id)
    except ResearchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return ResearchDetailResponse.model_validate(query)


@router.delete("/{query_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_research(
    query_id: str,
    session: AsyncSession = Depends(db_session),
    user: User = Depends(get_current_user),
) -> None:
    try:
        await ResearchService(session).delete(query_id=query_id, user_id=user.id)
    except ResearchNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

