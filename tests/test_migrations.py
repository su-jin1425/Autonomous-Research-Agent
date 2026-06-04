from pathlib import Path

from sqlalchemy import create_engine, inspect

from alembic import command
from alembic.config import Config
from app.core.config import get_settings


def test_alembic_upgrade_head(tmp_path, monkeypatch) -> None:
    database_path = (tmp_path / "migrations.db").resolve()
    database_url = f"sqlite+aiosqlite:///{database_path.as_posix()}"
    sync_url = f"sqlite:///{database_path.as_posix()}"

    monkeypatch.setenv("ENVIRONMENT", "local")
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_settings.cache_clear()

    config = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))

    try:
        command.upgrade(config, "head")
    finally:
        get_settings.cache_clear()

    engine = create_engine(sync_url)
    inspector = inspect(engine)

    assert {"users", "research_queries", "research_reports"}.issubset(set(inspector.get_table_names()))
    assert any(index["name"] == "ix_users_email" for index in inspector.get_indexes("users"))
