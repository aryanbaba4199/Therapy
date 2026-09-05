"""Constants and enumerations for the Package domain."""

from enum import StrEnum


class PackageStatus(StrEnum):
    """User package entitlement status."""

    ACTIVE = "active"
    EXHAUSTED = "exhausted"
    EXPIRED = "expired"
