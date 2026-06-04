import pytest

from app.api.routes import research as research_routes


@pytest.fixture
def noop_research_job(monkeypatch):
    async def _noop(*args, **kwargs):
        return None

    monkeypatch.setattr(research_routes, "execute_research_job", _noop)


@pytest.mark.asyncio
async def test_research_api_supports_create_list_detail_and_delete(
    client,
    auth_headers,
    async_session,
    noop_research_job,
) -> None:
    start_response = client.post(
        "/api/v1/research/start",
        headers=auth_headers,
        json={
            "query": "Future of autonomous research agents",
            "max_sources": 3,
            "max_depth": 1,
            "async_execution": False,
        },
    )

    assert start_response.status_code == 202

    query_id = start_response.json()["id"]

    list_response = client.get(
        "/api/v1/research",
        headers=auth_headers,
    )
    status_response = client.get(
        f"/api/v1/research/status/{query_id}",
        headers=auth_headers,
    )
    detail_response = client.get(
        f"/api/v1/research/{query_id}",
        headers=auth_headers,
    )
    delete_response = client.delete(
        f"/api/v1/research/{query_id}",
        headers=auth_headers,
    )

    assert list_response.status_code == 200
    assert status_response.status_code == 200
    assert detail_response.status_code == 200
    assert delete_response.status_code == 204
    assert any(item["id"] == query_id for item in list_response.json())


@pytest.mark.asyncio
async def test_research_api_returns_404_for_missing_query(client, auth_headers) -> None:
    response = client.get(
        "/api/v1/research/status/missing-query-id",
        headers=auth_headers,
    )

    assert response.status_code == 404
