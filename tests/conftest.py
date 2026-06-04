import asyncio
import shutil
from pathlib import Path

import pytest

from app.db.session import init_db


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