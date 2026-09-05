"""User domain constants and enumerations."""

from enum import StrEnum


class UserRole(StrEnum):
    """Supported user roles in the platform."""

    USER = "user"
    THERAPIST = "therapist"
    STAFF = "staff"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class UserStatus(StrEnum):
    """Operational status of a user account."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class AuthProvider(StrEnum):
    """Authentication mechanisms linked to a user account."""

    PASSWORD = "password"
    OTP = "otp"
    GOOGLE = "google"
