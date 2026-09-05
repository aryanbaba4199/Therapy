"""Application exception hierarchy with structured error codes."""

from typing import Any

from app.common.exceptions.error_codes import ErrorCode


class AppException(Exception):
    """Base exception for all controlled application errors."""

    def __init__(
        self,
        message: str = "An unexpected error occurred",
        code: ErrorCode | str = ErrorCode.INTERNAL_SERVER_ERROR,
        status_code: int = 500,
        details: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.code = code.value if isinstance(code, ErrorCode) else code
        self.status_code = status_code
        self.details = details


class BusinessException(AppException):
    """Exception raised when a business logic rule is violated."""

    def __init__(
        self,
        message: str,
        code: ErrorCode | str = ErrorCode.BUSINESS_RULE_VIOLATION,
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=400,
            details=details,
        )


class NotFoundException(AppException):
    """Exception raised when a requested resource is not found."""

    def __init__(
        self,
        message: str = "Resource not found",
        code: ErrorCode | str = ErrorCode.NOT_FOUND,
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=404,
            details=details,
        )


class UnauthorizedException(AppException):
    """Exception raised when authentication fails or is absent."""

    def __init__(
        self,
        message: str = "Authentication required",
        code: ErrorCode | str = ErrorCode.UNAUTHORIZED,
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=401,
            details=details,
        )


class ForbiddenException(AppException):
    """Exception raised when the client lacks required permissions."""

    def __init__(
        self,
        message: str = "Access denied",
        code: ErrorCode | str = ErrorCode.FORBIDDEN,
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=403,
            details=details,
        )


class ConflictException(AppException):
    """Exception raised when an operation conflicts with existing state."""

    def __init__(
        self,
        message: str = "Resource conflict occurred",
        code: ErrorCode | str = ErrorCode.CONFLICT,
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=409,
            details=details,
        )


class ValidationException(AppException):
    """Exception raised when request data validation fails."""

    def __init__(
        self,
        message: str = "Validation failed",
        code: ErrorCode | str = ErrorCode.VALIDATION_ERROR,
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=422,
            details=details,
        )


class BadRequestException(AppException):
    """Exception raised for general malformed or illegal client operations."""

    def __init__(
        self,
        message: str = "Bad request",
        code: ErrorCode | str = ErrorCode.BAD_REQUEST,
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=400,
            details=details,
        )


class RateLimitedException(AppException):
    """Exception raised when client exceeds rate limits or cooldown periods."""

    def __init__(
        self,
        message: str = "Too many requests. Please slow down.",
        code: ErrorCode | str = ErrorCode.AUTH_OTP_RATE_LIMITED,
        details: Any | None = None,
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=429,
            details=details,
        )
