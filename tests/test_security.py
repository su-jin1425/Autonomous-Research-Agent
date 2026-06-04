from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from jose import jwt

from app.core.config import get_settings
from app.core.security import (
    ALGORITHM,
    ISSUER,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    hash_password,
    verify_password,
)
from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def register_and_login(client: TestClient) -> tuple[str, str]:
    email = f"security_{uuid4().hex}@example.com"

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Security User",
            "email": email,
            "password": "StrongPassword123",
            "role": "researcher",
        },
    )

    assert register_response.status_code == 201

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": "StrongPassword123",
        },
    )

    assert login_response.status_code == 200

    payload = login_response.json()
    return payload["access_token"], payload["refresh_token"]


def test_hash_password_creates_different_value() -> None:
    password = "StrongPassword123"

    hashed = hash_password(password)

    assert hashed != password
    assert isinstance(hashed, str)


def test_verify_password_success() -> None:
    password = "StrongPassword123"

    hashed = hash_password(password)

    assert verify_password(
        password,
        hashed,
    )


def test_verify_password_failure() -> None:
    password = "StrongPassword123"

    hashed = hash_password(password)

    assert not verify_password(
        "WrongPassword",
        hashed,
    )


def test_create_access_token() -> None:
    token = create_access_token(
        "user-123",
        {
            "role": "researcher",
        },
    )

    assert isinstance(token, str)
    assert len(token) > 20


def test_create_refresh_token() -> None:
    token = create_refresh_token(
        "user-123",
    )

    assert isinstance(token, str)
    assert len(token) > 20


def test_decode_access_token() -> None:
    token = create_access_token(
        "user-123",
        {
            "role": "researcher",
        },
    )

    payload = decode_access_token(token)

    assert payload["sub"] == "user-123"
    assert payload["type"] == "access"
    assert payload["role"] == "researcher"


def test_decode_refresh_token() -> None:
    token = create_refresh_token(
        "user-123",
    )

    payload = decode_refresh_token(token)

    assert payload["sub"] == "user-123"
    assert payload["type"] == "refresh"


def test_access_token_rejects_refresh_token() -> None:
    token = create_refresh_token(
        "user-123",
    )

    with pytest.raises(ValueError):
        decode_access_token(token)


def test_refresh_token_rejects_access_token() -> None:
    token = create_access_token(
        "user-123",
    )

    with pytest.raises(ValueError):
        decode_refresh_token(token)


def test_invalid_token_rejected() -> None:
    with pytest.raises(ValueError):
        decode_access_token(
            "this-is-not-a-valid-token",
        )


def test_expired_token_rejected() -> None:
    settings = get_settings()

    now = datetime.now(UTC)

    payload = {
        "sub": "user-123",
        "type": "access",
        "iss": ISSUER,
        "iat": now - timedelta(hours=2),
        "nbf": now - timedelta(hours=2),
        "exp": now - timedelta(hours=1),
    }

    token = jwt.encode(
        payload,
        settings.secret_key,
        algorithm=ALGORITHM,
    )

    with pytest.raises(ValueError):
        decode_access_token(token)


def test_invalid_token_type_rejected() -> None:
    settings = get_settings()

    now = datetime.now(UTC)

    payload = {
        "sub": "user-123",
        "type": "invalid",
        "iss": ISSUER,
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(minutes=30),
    }

    token = jwt.encode(
        payload,
        settings.secret_key,
        algorithm=ALGORITHM,
    )

    with pytest.raises(ValueError):
        decode_access_token(token)


def test_wrong_issuer_rejected() -> None:
    settings = get_settings()

    now = datetime.now(UTC)

    payload = {
        "sub": "user-123",
        "type": "access",
        "iss": "wrong-issuer",
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(minutes=30),
    }

    token = jwt.encode(
        payload,
        settings.secret_key,
        algorithm=ALGORITHM,
    )

    with pytest.raises(ValueError):
        decode_access_token(token)


def test_access_token_contains_custom_claims() -> None:
    token = create_access_token(
        "user-123",
        {
            "role": "admin",
            "email": "admin@example.com",
        },
    )

    payload = decode_access_token(token)

    assert payload["role"] == "admin"
    assert payload["email"] == "admin@example.com"


def test_refresh_token_contains_subject() -> None:
    token = create_refresh_token(
        "refresh-user",
    )

    payload = decode_refresh_token(token)

    assert payload["sub"] == "refresh-user"


def test_refresh_token_is_rejected_by_protected_endpoints(client: TestClient) -> None:
    access_token, refresh_token = register_and_login(client)

    access_response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )
    refresh_response = client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {refresh_token}",
        },
    )

    assert access_response.status_code == 200
    assert refresh_response.status_code == 401
