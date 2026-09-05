"""Tests for request ID, logging, and exception middleware behavior."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_custom_request_id_propagation(client: AsyncClient) -> None:
    """Verify client-supplied X-Request-ID is preserved and reflected in response."""
    custom_id = "test-custom-request-id-12345"
    response = await client.get("/api/v1/health", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == custom_id
    payload = response.json()
    assert payload["request_id"] == custom_id


@pytest.mark.asyncio
async def test_not_found_exception_handling(client: AsyncClient) -> None:
    """Verify non-existent routes return 404 with unified error envelope."""
    response = await client.get("/api/v1/non-existent-endpoint")
    assert response.status_code == 404

    payload = response.json()
    assert payload["success"] is False
    assert payload["data"] is None
    assert payload["error"] is not None
    assert payload["error"]["code"] == "NOT_FOUND"
    assert payload["request_id"] is not None
