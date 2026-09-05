"""Unit tests for standardized API response envelopes."""

from app.common.responses.api_response import error_response, success_response


def test_success_response_builder() -> None:
    """Verify success response structure."""
    resp = success_response(data={"key": "val"}, message="Done", request_id="req-123")
    assert resp.success is True
    assert resp.message == "Done"
    assert resp.data == {"key": "val"}
    assert resp.error is None
    assert resp.request_id == "req-123"


def test_error_response_builder() -> None:
    """Verify error response structure."""
    resp = error_response(
        message="Failure",
        code="SOME_ERROR",
        details={"field": "missing"},
        request_id="req-456",
    )
    assert resp.success is False
    assert resp.data is None
    assert resp.error is not None
    assert resp.error.code == "SOME_ERROR"
    assert resp.error.details == {"field": "missing"}
    assert resp.request_id == "req-456"
