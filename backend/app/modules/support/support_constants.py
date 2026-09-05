"""Support domain constants and enumerations."""

from enum import StrEnum


class SupportCategory(StrEnum):
    """Categorization of client/therapist support inquiries."""

    BOOKING = "booking"
    PAYMENT = "payment"
    THERAPIST = "therapist"
    SESSION = "session"
    PACKAGE = "package"
    ACCOUNT = "account"
    TECHNICAL = "technical"
    OTHER = "other"


class SupportPriority(StrEnum):
    """Priority levels for support ticket SLA routing."""

    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class SupportTicketStatus(StrEnum):
    """Operational lifecycle state machine for support tickets."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_FOR_USER = "waiting_for_user"
    RESOLVED = "resolved"
    CLOSED = "closed"
