"""Security abstractions and type-safe helpers."""

import hashlib
import hmac
from datetime import UTC, datetime, timedelta

from app.core.config import get_settings


def generate_secure_hash(data: str) -> str:
    """Generate a SHA-256 HMAC for secure token comparisons or deterministic identifiers."""
    settings = get_settings()
    return hmac.new(
        settings.jwt_secret_key.encode("utf-8"),
        data.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def compute_token_expiry(duration_minutes: int | None = None) -> datetime:
    """Compute standard UTC expiration timestamp."""
    settings = get_settings()
    minutes = (
        duration_minutes
        if duration_minutes is not None
        else settings.jwt_access_token_expire_minutes
    )
    return datetime.now(UTC) + timedelta(minutes=minutes)
