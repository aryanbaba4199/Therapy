"""Unit tests for application configuration."""

from app.core.config import Settings, get_settings


def test_settings_initialization() -> None:
    """Verify settings defaults and types."""
    settings = get_settings()
    assert isinstance(settings, Settings)
    assert settings.api_v1_prefix == "/api/v1"
    assert settings.app_version == "1.0.0"
    assert isinstance(settings.cors_origins, list)
    assert settings.request_id_header == "X-Request-ID"
