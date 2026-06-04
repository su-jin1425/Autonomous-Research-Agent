from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

ResearchStatus = Literal["queued", "running", "completed", "failed", "cancelled"]


class ResearchStartRequest(BaseModel):
    query: str = Field(min_length=5, max_length=4000)
    max_sources: int = Field(default=6, ge=1, le=20)
    max_depth: int = Field(default=2, ge=1, le=4)
    async_execution: bool = True


class ResearchSourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_url: str
    source_title: str | None
    quality_score: float


class ResearchReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    generated_summary: str
    report_payload: dict[str, Any]
    created_at: datetime


class ResearchQueryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    query: str
    status: ResearchStatus
    created_at: datetime
    completed_at: datetime | None


class ResearchDetailResponse(ResearchQueryResponse):
    sources: list[ResearchSourceResponse] = []
    report: ResearchReportResponse | None = None
