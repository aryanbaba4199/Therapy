"""Constants and enumerations for the Payment domain."""

from enum import StrEnum


class PaymentStatus(StrEnum):
    """Lifecycle states of a commercial payment."""

    CREATED = "created"
    PENDING = "pending"
    AUTHORIZED = "authorized"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentMethod(StrEnum):
    """Supported transaction methods."""

    UPI = "upi"
    CARD = "card"
    NETBANKING = "netbanking"
    WALLET = "wallet"
    PACKAGE_REDEMPTION = "package_redemption"
    MOCK = "mock"


class PaymentTargetType(StrEnum):
    """Target entity being purchased."""

    BOOKING = "booking"
    PACKAGE = "package"


class PaymentProviderName(StrEnum):
    """Supported payment gateway integrations."""

    MOCK = "mock"
    RAZORPAY = "razorpay"
    CASHFREE = "cashfree"
    STRIPE = "stripe"
