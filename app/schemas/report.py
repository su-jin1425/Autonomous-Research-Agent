from typing import Any, Literal

from pydantic import BaseModel


class ReportExportRequest(BaseModel):
    report_id: str
    format: Literal["json", "markdown"] = "markdown"


class ReportExportResponse(BaseModel):
    report_id: str
    format: str
    content: dict[str, Any] | str
