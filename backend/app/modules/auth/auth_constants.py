"""Authentication domain constants and enumerations."""

from enum import StrEnum


class TokenType(StrEnum):
    """JWT token classification."""

    ACCESS = "access"
    REFRESH = "refresh"


class OtpChannel(StrEnum):
    """Delivery channels for OTP verification codes."""

    WHATSAPP = "whatsapp"
    SMS = "sms"


class OtpStatus(StrEnum):
    """Lifecycle states of an OTP verification cycle."""

    PENDING = "pending"
    VERIFIED = "verified"
    EXPIRED = "expired"
    FAILED = "failed"
