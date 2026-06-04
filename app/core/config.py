from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


DEFAULT_SECRET_KEY = "local-development-secret-key-32chars"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Autonomous Research Agent V2"

    environment: Literal[
        "local",
        "test",
        "staging",
        "production",
    ] = "local"

    debug: bool = False

    api_v1_prefix: str = "/api/v1"

    database_url: str = "postgresql://postgres:postgres@postgres:5432/research_agent"

    redis_url: str = "redis://redis:6379/0"

    chroma_persist_dir: str = "./data/chroma"

    faiss_index_path: str = "./data/faiss/research.index"

    secret_key: str = Field(
        default=DEFAULT_SECRET_KEY,
        min_length=32,
    )

    access_token_expire_minutes: int = 30

    refresh_token_expire_minutes: int = 60 * 24 * 7

    password_hash_rounds: int = 12

    openai_api_key: str | None = None

    llm_model: str = "gpt-4o-mini"

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
    ]

    rate_limit_requests: int = 120

    rate_limit_window_seconds: int = 60

    auto_create_tables: bool = True

    use_celery: bool = False

    research_max_sources: int = 6

    research_max_depth: int = 2

    browser_timeout_ms: int = 15000

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [
                origin.strip()
                for origin in value.split(",")
                if origin.strip()
            ]
        return value

    @field_validator("access_token_expire_minutes")
    @classmethod
    def validate_access_expiry(cls, value: int) -> int:
        if value <= 0:
            raise ValueError(
                "access_token_expire_minutes must be greater than zero"
            )
        return value

    @field_validator("refresh_token_expire_minutes")
    @classmethod
    def validate_refresh_expiry(cls, value: int) -> int:
        if value <= 0:
            raise ValueError(
                "refresh_token_expire_minutes must be greater than zero"
            )
        return value

    @field_validator("redis_url")
    @classmethod
    def validate_redis_url(cls, value: str) -> str:
        if not value.startswith(("redis://", "rediss://")):
            raise ValueError(
                "redis_url must use redis:// or rediss://"
            )
        return value

    @model_validator(mode="after")
    def validate_environment_configuration(self):
        if self.environment == "production":
            if self.secret_key == DEFAULT_SECRET_KEY:
                raise ValueError(
                    "Production requires a custom SECRET_KEY"
                )

            if "sqlite" in self.database_url.lower():
                raise ValueError(
                    "SQLite is not permitted in production"
                )

        return self

    @property
    def async_database_url(self) -> str:
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace(
                "postgresql://",
                "postgresql+asyncpg://",
                1,
            )

        return self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()