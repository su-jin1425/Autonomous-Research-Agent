import time

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def admin_headers(client):
    email = f"admin_{int(time.time())}@example.com"

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Admin User",
            "email": email,
            "password": "StrongPassword123",
            "role": "researcher"
        },
    )

    assert register_response.status_code in [201, 409]

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "StrongPassword123",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}",
    }


def test_health_endpoint(client):
    response = client.get(
        "/api/v1/monitoring/health",
    )

    assert response.status_code == 200

    data = response.json()

    assert "status" in data
    assert "environment" in data
    assert "database" in data
    assert "redis" in data


def test_metrics_endpoint(client):
    response = client.get(
        "/api/v1/monitoring/metrics",
    )

    assert response.status_code == 200

    assert "research_runs_total" in response.text


def test_prometheus_content_type(client):
    response = client.get(
        "/api/v1/monitoring/metrics",
    )

    assert response.status_code == 200

    assert (
        "text/plain"
        in response.headers["content-type"]
    )


def test_execution_metrics_requires_auth(client):
    response = client.get(
        "/api/v1/monitoring/executions",
    )

    assert response.status_code in [
        401,
        403,
    ]


def test_execution_metrics_authenticated(
    client,
    admin_headers,
):
    response = client.get(
        "/api/v1/monitoring/executions",
        headers=admin_headers,
    )

    assert response.status_code in [
        200,
        403,
    ]


def test_health_response_schema(client):
    response = client.get(
        "/api/v1/monitoring/health",
    )

    data = response.json()

    assert isinstance(
        data["status"],
        str,
    )

    assert isinstance(
        data["environment"],
        str,
    )

    assert isinstance(
        data["database"],
        str,
    )

    assert isinstance(
        data["redis"],
        str,
    )


def test_metrics_endpoint_contains_custom_metrics(
    client,
):
    response = client.get(
        "/api/v1/monitoring/metrics",
    )

    metrics_text = response.text

    expected_metrics = [
        "research_runs_total",
        "research_retrieval_documents_total",
        "research_execution_seconds",
        "vector_search_seconds",
    ]

    found = any(
        metric in metrics_text
        for metric in expected_metrics
    )

    assert found


def test_health_endpoint_is_reachable_multiple_times(
    client,
):
    for _ in range(3):
        response = client.get(
            "/api/v1/monitoring/health",
        )

        assert response.status_code == 200


def test_metrics_endpoint_is_reachable_multiple_times(
    client,
):
    for _ in range(3):
        response = client.get(
            "/api/v1/monitoring/metrics",
        )

        assert response.status_code == 200