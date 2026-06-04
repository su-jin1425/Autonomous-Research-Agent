from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.user import User
from app.retrieval.search import WebSearchClient
from app.schemas.retrieval import RetrievalHit, RetrievalSearchRequest, RetrievalSearchResponse


router = APIRouter(prefix="/retrieval", tags=["retrieval"])


@router.post("/search", response_model=RetrievalSearchResponse)
async def search_retrieval(
    request: RetrievalSearchRequest,
    _: User = Depends(get_current_user),
) -> RetrievalSearchResponse:
    documents = await WebSearchClient().search(request.query, limit=request.limit)
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

