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


class MeetingStatus(StrEnum):
    """Status for session video conference meeting provisioning."""

    NOT_REQUIRED = "not_required"
    NOT_STARTED = "not_started"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class MeetingProviderType(StrEnum):
    """Supported meeting provider backends."""

    GOOGLE_MEET = "google_meet"
    MOCK = "mock"

