from pydantic import BaseModel, Field


class RetrievalSearchRequest(BaseModel):
    query: str = Field(min_length=3, max_length=1000)
    limit: int = Field(default=5, ge=1, le=20)


class RetrievalHit(BaseModel):
    title: str | None = None
    url: str
    snippet: str
    score: float = 0.0


class RetrievalSearchResponse(BaseModel):
    query: str
    results: list[RetrievalHit]
