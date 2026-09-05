"""Booking and reservation domain enumerations and lifecycle transitions."""

from enum import StrEnum


class ReservationStatus(StrEnum):
    """Lifecycle status of a temporary slot reservation."""

    ACTIVE = "active"
    CONVERTED = "converted"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class BookingStatus(StrEnum):
    """Lifecycle operational status of a consultation booking."""

    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    NO_SHOW = "no_show"


VALID_RESERVATION_STATUS_TRANSITIONS: dict[ReservationStatus, set[ReservationStatus]] = {
    ReservationStatus.ACTIVE: {
        ReservationStatus.CONVERTED,
        ReservationStatus.EXPIRED,
        ReservationStatus.CANCELLED,
    },
    ReservationStatus.CONVERTED: set(),
    ReservationStatus.EXPIRED: set(),
    ReservationStatus.CANCELLED: set(),
}


VALID_BOOKING_STATUS_TRANSITIONS: dict[BookingStatus, set[BookingStatus]] = {
    BookingStatus.PENDING: {BookingStatus.CONFIRMED, BookingStatus.CANCELLED},
    BookingStatus.CONFIRMED: {
        BookingStatus.CANCELLED,
        BookingStatus.COMPLETED,
        BookingStatus.NO_SHOW,
    },
    BookingStatus.CANCELLED: set(),
    BookingStatus.COMPLETED: set(),
    BookingStatus.NO_SHOW: set(),
}
