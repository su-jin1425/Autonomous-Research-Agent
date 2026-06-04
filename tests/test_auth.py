import time

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def unique_email() -> str:
    return f"test_{int(time.time() * 1000000)}@example.com"


def test_register_user_success(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Test User",
            "email": unique_email(),
            "password": "StrongPassword123",
            "role": "researcher",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert "id" in data
    assert data["name"] == "Test User"
    assert data["role"] == "researcher"


def test_register_duplicate_user(client: TestClient) -> None:
    email = unique_email()

    payload = {
        "name": "Duplicate User",
        "email": email,
        "password": "StrongPassword123",
        "role": "researcher",
    }

    first = client.post(
        "/api/v1/auth/register",
        json=payload,
    )

    assert first.status_code == 201

    second = client.post(
        "/api/v1/auth/register",
        json=payload,
    )

    assert second.status_code == 409


def test_register_invalid_payload(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register",
        json={},
    )

    assert response.status_code == 422


def test_login_success(client: TestClient) -> None:
    email = unique_email()

    register = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Login User",
            "email": email,
            "password": "StrongPassword123",
            "role": "researcher",
        },
    )

    assert register.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "StrongPassword123",
        },
    )

    assert login.status_code == 200

    data = login.json()

    assert "access_token" in data
    assert "refresh_token" in data


def test_login_wrong_password(client: TestClient) -> None:
    email = unique_email()

    register = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Wrong Password User",
            "email": email,
            "password": "StrongPassword123",
            "role": "researcher",
        },
    )

    assert register.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "WrongPassword",
        },
    )

    assert login.status_code == 401


def test_login_unknown_user(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "missing@example.com",
            "password": "StrongPassword123",
        },
    )

    assert response.status_code == 401


def test_me_endpoint(client: TestClient) -> None:
    email = unique_email()

    register = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Profile User",
            "email": email,
            "password": "StrongPassword123",
            "role": "researcher",
        },
    )

    assert register.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "StrongPassword123",
        },
    )

    token = login.json()["access_token"]

    response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == email
    assert data["name"] == "Profile User"


def test_me_requires_authentication(client: TestClient) -> None:
    response = client.get(
        "/api/v1/auth/me",
    )

    assert response.status_code in [401, 403]


def test_refresh_not_implemented(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/refresh",
    )

    assert response.status_code == 501


def test_logout_not_implemented(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/logout",
    )

    assert response.status_code == 501