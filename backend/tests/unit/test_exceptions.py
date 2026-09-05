"""Unit tests for custom application exceptions."""

from app.common.exceptions.app_exceptions import (
    BusinessException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
    UnauthorizedException,
    ValidationException,
)
from app.common.exceptions.error_codes import ErrorCode


def test_custom_exceptions_attributes() -> None:
    """Verify exception status codes and error code assignments."""
    exc = BusinessException(message="Invalid transition", code=ErrorCode.BUSINESS_RULE_VIOLATION)
    assert exc.status_code == 400
    assert exc.code == ErrorCode.BUSINESS_RULE_VIOLATION.value
    assert exc.message == "Invalid transition"

    nf_exc = NotFoundException(message="Therapist not found", code="THERAPIST_NOT_FOUND")
    assert nf_exc.status_code == 404
    assert nf_exc.code == "THERAPIST_NOT_FOUND"

    unauth_exc = UnauthorizedException()
    assert unauth_exc.status_code == 401

    forb_exc = ForbiddenException()
    assert forb_exc.status_code == 403

    conf_exc = ConflictException()
    assert conf_exc.status_code == 409

    val_exc = ValidationException()
    assert val_exc.status_code == 422
