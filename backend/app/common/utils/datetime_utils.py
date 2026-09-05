"""Timezone-aware datetime utilities."""

from datetime import UTC, datetime


def utc_now() -> datetime:
    """Return current UTC datetime with timezone info."""
    return datetime.now(UTC)


def to_utc_iso(dt: datetime) -> str:
    """Format datetime to standard ISO 8601 UTC string."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).isoformat()
