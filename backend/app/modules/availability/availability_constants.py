"""Availability domain enumerations and constants."""

from enum import IntEnum, StrEnum


class DayOfWeek(IntEnum):
    """Zero-indexed day of week matching Python's datetime.weekday() (0=Monday, 6=Sunday)."""

    MONDAY = 0
    TUESDAY = 1
    WEDNESDAY = 2
    THURSDAY = 3
    FRIDAY = 4
    SATURDAY = 5
    SUNDAY = 6


class SlotStatus(StrEnum):
    """Lifecycle and reservation status for consultation slots."""

    AVAILABLE = "available"
    RESERVED = "reserved"
    BOOKED = "booked"
    BLOCKED = "blocked"
    EXPIRED = "expired"


# Canonical operational defaults
DEFAULT_TIMEZONE = "Asia/Kolkata"
MAX_SLOT_DISCOVERY_DAYS = 30
MIN_SESSION_DURATION_MINUTES = 15
MAX_SESSION_DURATION_MINUTES = 180
DEFAULT_BUFFER_MINUTES = 0

