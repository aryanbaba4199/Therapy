"""Integration tests for the health check endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint_success(client: AsyncClient) -> None:
    """Verify /api/v1/health returns 200 and standard response envelope."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200

    payload = response.json()
    assert payload["success"] is True
    assert "Platform health check completed" in payload["message"]
    assert "data" in payload
    assert payload["data"]["status"] in ("healthy", "degraded")
    assert payload["data"]["version"] == "1.0.0"
    assert "database" in payload["data"]
    assert payload["error"] is None
    assert payload["request_id"] is not None
    assert response.headers.get("X-Request-ID") == payload["request_id"]


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient) -> None:
    """Verify root endpoint responds with application info."""
    response = await client.get("/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert "data" in payload
    assert "version" in payload["data"]
