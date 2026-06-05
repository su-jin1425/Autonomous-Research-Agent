import asyncio
import os
import shutil
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

# Force test configuration and override .env values
os.environ["ENVIRONMENT"] = "test"

from app.db.session import AsyncSessionLocal, init_db
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    Path("test.db").unlink(missing_ok=True)

    shutil.rmtree("data/chroma", ignore_errors=True)
    shutil.rmtree("data/faiss", ignore_errors=True)
    shutil.rmtree("logs", ignore_errors=True)

    asyncio.run(init_db())

    yield

    Path("test.db").unlink(missing_ok=True)

    shutil.rmtree("data/chroma", ignore_errors=True)
    shutil.rmtree("data/faiss", ignore_errors=True)
    shutil.rmtree("logs", ignore_errors=True)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def async_session():
    async with AsyncSessionLocal() as session:
        yield session


@pytest.fixture
def auth_headers(client):
    email = f"test_{uuid4().hex}@example.com"

    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "name": "Test User",
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

    return {
        "Authorization": f"Bearer {login_response.json()['access_token']}",
    }