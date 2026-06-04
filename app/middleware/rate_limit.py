from __future__ import annotations

from fastapi import status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings
from app.services.redis_service import RedisService


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app) -> None:
        super().__init__(app)

        self.settings = get_settings()
        self.redis = RedisService()

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Skip rate limiting for:
        - tests
        - health endpoints
        - readiness probes
        - liveness probes
        """

        if self.settings.environment == "test":
            return await call_next(request)

        if request.url.path.startswith("/health"):
            return await call_next(request)

        client_ip = (
            request.client.host
            if request.client
            else "unknown"
        )

        key = (
            f"rate-limit:"
            f"{client_ip}:"
            f"{request.url.path}"
        )

        allowed, count = await self.redis.increment_rate_limit(
            key=key,
            limit=self.settings.rate_limit_requests,
            window_seconds=self.settings.rate_limit_window_seconds,
        )

        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Rate limit exceeded",
                    "requests": count,
                },
            )

        response = await call_next(request)

        response.headers["X-RateLimit-Count"] = str(count)
        response.headers["X-RateLimit-Limit"] = str(
            self.settings.rate_limit_requests
        )

        return response