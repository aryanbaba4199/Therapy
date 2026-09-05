"""Request execution and performance logging middleware."""

import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.middleware.request_id_middleware import get_request_id

logger = logging.getLogger("app.middleware.logging")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log incoming requests, status codes, and execution duration."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.perf_counter()
        req_id = get_request_id()

        # Process the request
        response = await call_next(request)

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        # Don't spam logs for health checks unless in debug mode
        if not (request.url.path.endswith("/health") and response.status_code == 200):
            logger.info(
                "[%s] %s %s - %d (%.2fms)",
                req_id,
                request.method,
                request.url.path,
                response.status_code,
                duration_ms,
            )

        return response
