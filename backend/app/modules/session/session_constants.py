"""Constants and Enums for the Session Domain."""

from enum import StrEnum


class SessionStatus(StrEnum):
    """Operational status of a confirmed therapy session."""

    SCHEDULED = "scheduled"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


class AttendanceStatus(StrEnum):
    """Attendance record for a session."""

    UNKNOWN = "unknown"
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"


class GoalStatus(StrEnum):
    """Status for therapy goals."""

    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"
