"""Pytest fixtures and test environment configuration."""

import os

# Enforce test environment before importing application modules
os.environ["APP_ENV"] = "test"
os.environ["DEBUG"] = "true"
os.environ["MONGODB_DATABASE"] = "oppam_therapy_test"
os.environ["PAYMENT_PROVIDER"] = "mock"
os.environ["JWT_SECRET_KEY"] = "test-jwt-secret-key-that-is-at-least-32-chars-long-for-hmac-sha256"

from collections.abc import AsyncIterator  # noqa: E402
from typing import Any

import pytest  # noqa: E402
from fastapi import FastAPI  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from mongomock_motor import AsyncMongoMockClient  # noqa: E402

from app.core.config import Settings, get_settings  # noqa: E402
from app.database.mongodb import get_database  # noqa: E402
from app.main import create_app  # noqa: E402


@pytest.fixture(scope="session")
def settings() -> Settings:
    """Return application test settings."""
    return get_settings()


@pytest.fixture
def mock_db() -> Any:
    """Provide isolated in-memory MongoMock database for testing."""
    client: Any = AsyncMongoMockClient()
    return client["oppam_therapy_test"]


@pytest.fixture
def app(mock_db: Any) -> FastAPI:
    """Return a fresh FastAPI application instance with mocked database."""
    app_instance = create_app()
    app_instance.dependency_overrides[get_database] = lambda: mock_db
    return app_instance


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    """Asynchronous HTTP test client bound to ASGI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
