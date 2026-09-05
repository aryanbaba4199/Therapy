"""Request ID generation, propagation, and ContextVar tracking."""

import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import get_settings

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    """Retrieve the current request ID from context or generate a fallback."""
    rid = request_id_ctx.get()
    return rid if rid else uuid.uuid4().hex


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Middleware ensuring every request has a unique trace identifier."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        settings = get_settings()
        header_name = settings.request_id_header
        incoming_id = request.headers.get(header_name)

        req_id = incoming_id if incoming_id else uuid.uuid4().hex
        token = request_id_ctx.set(req_id)
        request.state.request_id = req_id

        try:
            response = await call_next(request)
            response.headers[header_name] = req_id
            return response
        finally:
            request_id_ctx.reset(token)
