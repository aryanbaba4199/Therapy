"""Standardized response envelope models and constructors."""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetails(BaseModel):
    """Machine-readable error structure contained in response envelopes."""

    code: str = Field(description="Stable machine-readable error code")
    details: Any | None = Field(
        default=None, description="Detailed validation or contextual errors"
    )


class ApiResponse(BaseModel, Generic[T]):
    """Universal API response envelope for all HTTP endpoints."""

    success: bool = Field(description="Indicates whether the request was successful")
    message: str = Field(description="Human or developer-readable message")
    data: T | None = Field(default=None, description="Payload data returned by the endpoint")
    meta: dict[str, Any] | None = Field(
        default=None, description="Metadata such as pagination or telemetry"
    )
    error: ErrorDetails | None = Field(
        default=None, description="Structured error details if success is False"
    )
    request_id: str | None = Field(
        default=None, description="Unique trace identifier for this request"
    )


def success_response(
    data: T | None = None,
    message: str = "Request completed successfully",
    meta: dict[str, Any] | None = None,
    request_id: str | None = None,
) -> ApiResponse[T]:
    """Helper to construct a standard successful ApiResponse envelope."""
    return ApiResponse[T](
        success=True,
        message=message,
        data=data,
        meta=meta,
        error=None,
        request_id=request_id,
    )


def error_response(
    message: str,
    code: str,
    details: Any | None = None,
    meta: dict[str, Any] | None = None,
    request_id: str | None = None,
) -> ApiResponse[None]:
    """Helper to construct a standard failed ApiResponse envelope."""
    return ApiResponse[None](
        success=False,
        message=message,
        data=None,
        meta=meta,
        error=ErrorDetails(code=code, details=details),
        request_id=request_id,
    )
