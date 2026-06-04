from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    environment: str
    database: str
    redis: str


class MetricsResponse(BaseModel):
    queued_research: int
    running_research: int
    completed_research: int
    failed_research: int
