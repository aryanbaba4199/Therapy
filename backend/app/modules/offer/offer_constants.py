"""Constants and enumerations for the Offer/Coupon domain."""

from enum import StrEnum


class DiscountType(StrEnum):
    """Supported mathematical discount models."""

    PERCENTAGE = "percentage"
    FIXED = "fixed"


class OfferStatus(StrEnum):
    """Operational status of promotional offers."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    EXHAUSTED = "exhausted"
