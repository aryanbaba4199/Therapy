"""Global exception handlers producing uniform API response envelopes."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.common.exceptions.app_exceptions import AppException
from app.common.exceptions.error_codes import ErrorCode
from app.common.responses.api_response import error_response
from app.core.config import get_settings
from app.middleware.request_id_middleware import get_request_id

logger = logging.getLogger("app.middleware.exceptions")


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle controlled application and domain exceptions."""
    req_id = getattr(request.state, "request_id", get_request_id())
    logger.warning("[%s] Business error: %s (code=%s)", req_id, exc.message, exc.code)

    payload = error_response(
        message=exc.message,
        code=exc.code,
        details=exc.details,
        request_id=req_id,
    )
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump())


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic/FastAPI request validation errors."""
    req_id = getattr(request.state, "request_id", get_request_id())

    # Format errors cleanly
    details = [
        {
            "loc": [str(loc) for loc in err.get("loc", [])],
            "msg": err.get("msg", "Invalid input"),
            "type": err.get("type", "value_error"),
        }
        for err in exc.errors()
    ]

    payload = error_response(
        message="Request validation failed",
        code=ErrorCode.VALIDATION_ERROR.value,
        details=details,
        request_id=req_id,
    )
    return JSONResponse(status_code=422, content=payload.model_dump())


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle standard HTTP exceptions like 404 Not Found or 405 Method Not Allowed."""
    req_id = getattr(request.state, "request_id", get_request_id())

    code_map = {
        404: ErrorCode.NOT_FOUND.value,
        401: ErrorCode.UNAUTHORIZED.value,
        403: ErrorCode.FORBIDDEN.value,
        400: ErrorCode.BAD_REQUEST.value,
    }
    error_code = code_map.get(exc.status_code, "HTTP_ERROR")

    payload = error_response(
        message=str(exc.detail),
        code=error_code,
        details=None,
        request_id=req_id,
    )
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump())


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch unexpected server errors safely without leaking internal stack traces."""
    req_id = getattr(request.state, "request_id", get_request_id())
    logger.exception("[%s] Unhandled exception occurred: %s", req_id, exc)

    settings = get_settings()
    message = str(exc) if settings.debug else "An unexpected internal server error occurred"

    payload = error_response(
        message=message,
        code=ErrorCode.INTERNAL_SERVER_ERROR.value,
        details=None,
        request_id=req_id,
    )
    return JSONResponse(status_code=500, content=payload.model_dump())


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all exception handlers to the FastAPI application."""
    app.add_exception_handler(AppException, app_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, unhandled_exception_handler)
