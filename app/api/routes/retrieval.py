import logging

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.user import User
from app.retrieval.search import SearchProviderError, WebSearchClient
from app.schemas.retrieval import RetrievalHit, RetrievalSearchRequest, RetrievalSearchResponse

router = APIRouter(prefix="/retrieval", tags=["retrieval"])
logger = logging.getLogger(__name__)


@router.post("/search", response_model=RetrievalSearchResponse)
async def search_retrieval(
    request: RetrievalSearchRequest,
    _: User = Depends(get_current_user),
) -> RetrievalSearchResponse:
    try:
        documents = await WebSearchClient().search(request.query, limit=request.limit)
    except SearchProviderError:
        logger.warning("Search provider unavailable", extra={"query": request.query})
        documents = []
    return RetrievalSearchResponse(
        query=request.query,
        results=[
            RetrievalHit(title=document.title, url=document.url, snippet=document.content[:500], score=document.score)
            for document in documents
        ],
    )


@router.get("/history")
async def retrieval_history(_: User = Depends(get_current_user)) -> dict[str, list]:
    return {"history": []}
