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
        if request.url.path.endswith("/health"):
            return await call_next(request)
        client = request.client.host if request.client else "unknown"
        key = f"rate-limit:{client}:{request.url.path}"
        allowed, count = await self.redis.increment_rate_limit(
            key,
            limit=self.settings.rate_limit_requests,
            window_seconds=self.settings.rate_limit_window_seconds,
        )
        if not allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded", "requests": count},
            )
        return await call_next(request)
