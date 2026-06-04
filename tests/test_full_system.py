import time

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(client):
    register_payload = {
        "name": "Test User",
        "email": f"test_{int(time.time())}@example.com",
        "password": "StrongPassword123",
        "role": "researcher",
    }

    register_response = client.post(
        "/api/v1/auth/register",
        json=register_payload,
    )

    assert register_response.status_code in [201, 409]

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": register_payload["email"],
            "password": register_payload["password"],
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}",
    }


def test_root(client):
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "running"


def test_liveness(client):
    response = client.get("/health/live")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "alive"


def test_readiness(client):
    response = client.get("/health/ready")

    assert response.status_code == 200

    data = response.json()

    assert "status" in data


def test_auth_me(client, auth_headers):
    response = client.get(
        "/api/v1/auth/me",
        headers=auth_headers,
    )

    assert response.status_code == 200


def test_monitoring_health(client, auth_headers):
    response = client.get(
        "/api/v1/monitoring/health",
        headers=auth_headers,
    )

    assert response.status_code == 200


def test_monitoring_metrics(client):
    response = client.get(
        "/api/v1/monitoring/metrics",
    )

    assert response.status_code == 200


def test_retrieval_search(client, auth_headers):
    response = client.post(
        "/api/v1/retrieval/search",
        headers=auth_headers,
        json={
            "query": "FastAPI",
            "limit": 5,
        },
    )

    assert response.status_code == 200


def test_research_workflow(client, auth_headers):
    start_response = client.post(
        "/api/v1/research/start",
        headers=auth_headers,
        json={
            "query": "Future of AI Agents",
            "max_sources": 3,
            "max_depth": 1,
            "async_execution": False,
        },
    )

    assert start_response.status_code in [200, 202]

    research = start_response.json()

    query_id = research["id"]

    status_response = client.get(
        f"/api/v1/research/status/{query_id}",
        headers=auth_headers,
    )

    assert status_response.status_code == 200

    detail_response = client.get(
        f"/api/v1/research/{query_id}",
        headers=auth_headers,
    )

    assert detail_response.status_code == 200

    detail = detail_response.json()

    report = detail.get("report")

    if report:
        report_id = report["id"]

        report_response = client.get(
            f"/api/v1/reports/{report_id}",
            headers=auth_headers,
        )

        assert report_response.status_code == 200

        export_response = client.post(
            "/api/v1/reports/export",
            headers=auth_headers,
            json={
                "report_id": report_id,
                "format": "markdown",
            },
        )

        assert export_response.status_code == 200

    delete_response = client.delete(
        f"/api/v1/research/{query_id}",
        headers=auth_headers,
    )

    assert delete_response.status_code in [200, 204]


def test_validation_errors(client):
    response = client.post(
        "/api/v1/auth/register",
        json={},
    )

    assert response.status_code == 422

    response = client.post(
        "/api/v1/research/start",
        json={
            "query": "a",
        },
    )

    assert response.status_code in [401, 422]