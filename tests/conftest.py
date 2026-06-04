import shutil
from pathlib import Path

import pytest


@pytest.fixture(scope="session", autouse=True)
def cleanup_before_and_after_session():
    Path("test.db").unlink(missing_ok=True)

    shutil.rmtree("data/chroma", ignore_errors=True)
    shutil.rmtree("data/faiss", ignore_errors=True)
    shutil.rmtree("logs", ignore_errors=True)

    yield

    Path("test.db").unlink(missing_ok=True)

    shutil.rmtree("data/chroma", ignore_errors=True)
    shutil.rmtree("data/faiss", ignore_errors=True)
    shutil.rmtree("logs", ignore_errors=True)