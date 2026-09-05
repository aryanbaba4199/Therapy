"""Middleware pipeline configuration and setup."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.middleware.exception_middleware import register_exception_handlers
from app.middleware.logging_middleware import LoggingMiddleware
from app.middleware.request_id_middleware import RequestIdMiddleware


def setup_middlewares(app: FastAPI) -> None:
    """Configure middleware stack in proper execution order."""
    settings = get_settings()

    # Exception Handlers (registered on FastAPI app)
    register_exception_handlers(app)

    # Logging Middleware (executes after request ID is set)
    app.add_middleware(LoggingMiddleware)

    # Request ID Middleware (outermost for tracking full lifecycle)
    app.add_middleware(RequestIdMiddleware)

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=settings.cors_allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )
