import asyncio
from typing import Any

from app.core.config import get_settings
from app.services.research_service import execute_research_job


settings = get_settings()

try:
    from celery import Celery
except ImportError:
    Celery = None  # type: ignore[assignment]


class _MissingCeleryTask:
    def delay(self, *_: Any, **__: Any) -> None:
        raise RuntimeError("Celery is not installed. Install dependencies or set USE_CELERY=false.")


if Celery is not None:
    celery_app = Celery("research_agent", broker=settings.redis_url, backend=settings.redis_url)
    celery_app.conf.task_routes = {"app.tasks.run_research": {"queue": "research"}}
else:
    celery_app = None


def run_research(query_id: str, max_sources: int, max_depth: int) -> None:
    asyncio.run(execute_research_job(query_id, max_sources=max_sources, max_depth=max_depth))


if celery_app is not None:
    run_research = celery_app.task(  # type: ignore[method-assign]
        name="app.tasks.run_research",
        autoretry_for=(Exception,),
        retry_backoff=True,
        max_retries=3,
    )(run_research)
else:
    run_research = _MissingCeleryTask()  # type: ignore[assignment]
