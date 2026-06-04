import shutil
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def cleanup_after_test():
    yield

    try:
        Path("test.db").unlink(missing_ok=True)
    except Exception:
        pass


@pytest.fixture(scope="session", autouse=True)
def cleanup_after_session():
    yield

    shutil.rmtree("data/chroma", ignore_errors=True)
    shutil.rmtree("data/faiss", ignore_errors=True)
    shutil.rmtree("logs", ignore_errors=True)