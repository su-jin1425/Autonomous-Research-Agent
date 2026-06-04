import shutil
import os
import pytest
from pathlib import Path


@pytest.fixture(scope="session", autouse=True)
def cleanup_after_tests():

    yield

    try:
        Path("test.db").unlink(missing_ok=True)
    except:
        pass

    shutil.rmtree("data/chroma", ignore_errors=True)

    shutil.rmtree("data/faiss", ignore_errors=True)

    shutil.rmtree("logs", ignore_errors=True)