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


def ensure_utc(dt: datetime) -> datetime:
    """Ensure datetime has UTC tzinfo, assuming naive datetimes are in UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)
