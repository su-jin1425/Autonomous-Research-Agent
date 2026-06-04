from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    auth,
    monitoring,
    notifications,
    reports,
    research,
    retrieval,
)
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import engine, init_db
from app.middleware.metrics import MetricsMiddleware
from app.middleware.rate_limit import RateLimitMiddleware

APP_VERSION = "0.2.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()

    if (
        settings.auto_create_tables
        and settings.environment != "test"
    ):
        await init_db()

    yield

    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()

    configure_logging()

    app = FastAPI(
        title=settings.app_name,
        version=APP_VERSION,
        debug=settings.debug,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_middleware(
        MetricsMiddleware,
    )

    app.add_middleware(
        RateLimitMiddleware,
    )

    app.include_router(
        auth.router,
        prefix=settings.api_v1_prefix,
    )

    app.include_router(
        research.router,
        prefix=settings.api_v1_prefix,
    )

    app.include_router(
        notifications.router,
        prefix=settings.api_v1_prefix,
    )

    app.include_router(
        retrieval.router,
        prefix=settings.api_v1_prefix,
    )

    app.include_router(
        reports.router,
        prefix=settings.api_v1_prefix,
    )

    app.include_router(
        monitoring.router,
        prefix=settings.api_v1_prefix,
    )

    @app.get("/")
    async def root() -> dict[str, str]:
        return {
            "name": settings.app_name,
            "version": APP_VERSION,
            "status": "running",
        }

    @app.get("/health/live")
    async def liveness() -> dict[str, str]:
        return {
            "status": "alive",
        }

    @app.get("/health/ready")
    async def readiness() -> dict[str, str]:
        try:
            async with engine.connect() as conn:
                await conn.exec_driver_sql("SELECT 1")

            return {
                "status": "ready",
                "database": "healthy",
            }

        except Exception as exc:
            return {
                "status": "not_ready",
                "database": str(exc),
            }

    return app


app = create_app()