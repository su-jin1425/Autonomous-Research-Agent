from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import db_session, get_current_user
from app.models.user import User
from app.repositories.research_repository import ResearchRepository
from app.schemas.report import ReportExportRequest, ReportExportResponse
from app.schemas.research import ResearchReportResponse

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/{report_id}", response_model=ResearchReportResponse)
async def get_report(
    report_id: str,
    session: AsyncSession = Depends(db_session),
    _: User = Depends(get_current_user),
) -> ResearchReportResponse:
    report = await ResearchRepository(session).get_report(report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    return ResearchReportResponse.model_validate(report)


@router.post("/export", response_model=ReportExportResponse)
async def export_report(
    request: ReportExportRequest,
    session: AsyncSession = Depends(db_session),
    _: User = Depends(get_current_user),
) -> ReportExportResponse:
    report = await ResearchRepository(session).get_report(request.report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    if request.format == "json":
        content = report.report_payload
    else:
        payload = report.report_payload
        findings = payload.get("key_findings", [])
        lines = ["# Research Report", "", report.generated_summary, "", "## Key Findings"]
        lines.extend(f"- {item}" if isinstance(item, str) else f"- {item.get('finding', '')}" for item in findings)
        lines.extend(["", "## Citations"])
        lines.extend(
            f"- {citation.get('title', '')}: {citation.get('url', '')}" for citation in payload.get("citations", [])
        )
        content = "\n".join(lines)
    return ReportExportResponse(report_id=report.id, format=request.format, content=content)
