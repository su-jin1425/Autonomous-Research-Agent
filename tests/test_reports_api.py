import pytest

from app.repositories.research_repository import ResearchRepository


@pytest.mark.asyncio
async def test_reports_api_exports_reports(client, auth_headers, async_session) -> None:
    repository = ResearchRepository(async_session)

    query = await repository.create_query(query="Report export test", user_id=None)
    report = await repository.save_report(
        query_id=query.id,
        payload={
            "executive_summary": "Summary",
            "key_findings": [
                {"finding": "FastAPI keeps the API simple."},
            ],
            "citations": [
                {"title": "Example", "url": "https://example.com"},
            ],
        },
        summary="Summary",
    )
    await async_session.commit()

    report_response = client.get(
        f"/api/v1/reports/{report.id}",
        headers=auth_headers,
    )
    export_markdown = client.post(
        "/api/v1/reports/export",
        headers=auth_headers,
        json={
            "report_id": report.id,
            "format": "markdown",
        },
    )
    export_json = client.post(
        "/api/v1/reports/export",
        headers=auth_headers,
        json={
            "report_id": report.id,
            "format": "json",
        },
    )

    assert report_response.status_code == 200
    assert report_response.json()["generated_summary"] == "Summary"
    assert export_markdown.status_code == 200
    assert "Research Report" in export_markdown.json()["content"]
    assert export_json.status_code == 200
    assert export_json.json()["content"]["executive_summary"] == "Summary"


@pytest.mark.asyncio
async def test_reports_api_returns_404_for_missing_report(client, auth_headers) -> None:
    response = client.get(
        "/api/v1/reports/missing-report-id",
        headers=auth_headers,
    )

    assert response.status_code == 404
