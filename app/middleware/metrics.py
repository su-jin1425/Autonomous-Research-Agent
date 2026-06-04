from time import perf_counter

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.monitoring.metrics import (
    HTTP_REQUEST_DURATION,
    HTTP_REQUEST_ERRORS_TOTAL,
    HTTP_REQUESTS_TOTAL,
)


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next,
    ) -> Response:
        start_time = perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            duration = perf_counter() - start_time

            HTTP_REQUEST_DURATION.observe(duration)
            HTTP_REQUESTS_TOTAL.labels(
                method=request.method,
                endpoint=request.url.path,
                status="500",
            ).inc()
            HTTP_REQUEST_ERRORS_TOTAL.labels(
                method=request.method,
                endpoint=request.url.path,
            ).inc()
            raise

        duration = perf_counter() - start_time

        HTTP_REQUEST_DURATION.observe(duration)
        HTTP_REQUESTS_TOTAL.labels(
            method=request.method,
            endpoint=request.url.path,
            status=str(response.status_code),
        ).inc()

        if response.status_code >= 500:
            HTTP_REQUEST_ERRORS_TOTAL.labels(
                method=request.method,
                endpoint=request.url.path,
            ).inc()

        return response
