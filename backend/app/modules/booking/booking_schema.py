"""Pydantic v2 schemas for Booking and Reservation requests and responses."""

import re
from datetime import UTC, datetime

from pydantic import BaseModel, Field, field_validator

from app.modules.booking.booking_constants import BookingStatus, ReservationStatus
from app.modules.booking.booking_model import (
    BookingInDB,
    ClientSnapshot,
    PricingSnapshot,
    ReservationInDB,
    TherapistSnapshot,
)
from app.modules.therapist.therapist_constants import SessionMode

DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class BookingMeetingResponse(BaseModel):
    """Sanitized meeting details attached to consultation booking."""

    provider: str
    status: str
    join_url: str | None = None


class CreateReservationRequest(BaseModel):
    """Payload to create a temporary slot reservation."""

    therapist_id: str = Field(description="Therapist UUID")
    slot_id: str = Field(description="Deterministic slot UUID")
    slot_date: str = Field(description="Consultation date in YYYY-MM-DD format")
    session_mode: SessionMode = Field(description="Selected delivery mode")

    @field_validator("slot_date")
    @classmethod
    def validate_date_format(cls, v: str) -> str:
        if not DATE_REGEX.match(v):
            raise ValueError("slot_date must be in YYYY-MM-DD format")
        return v


class ReservationResponse(BaseModel):
    """Reservation response payload."""

    id: str
    slot_id: str
    therapist_id: str
    client_id: str
    session_mode: SessionMode
    start_at: datetime
    end_at: datetime
    duration_minutes: int
    status: ReservationStatus
    expires_at: datetime
    seconds_remaining: int

    @classmethod
    def from_db(cls, doc: ReservationInDB) -> "ReservationResponse":
        now = datetime.now(UTC)
        diff = int((doc.expires_at - now).total_seconds())
        remaining = max(0, diff) if doc.status == ReservationStatus.ACTIVE else 0

        return cls(
            id=doc.id,
            slot_id=doc.slot_id,
            therapist_id=doc.therapist_id,
            client_id=doc.client_id,
            session_mode=doc.session_mode,
            start_at=doc.start_at,
            end_at=doc.end_at,
            duration_minutes=doc.duration_minutes,
            status=doc.status,
            expires_at=doc.expires_at,
            seconds_remaining=remaining,
        )


class ConfirmBookingRequest(BaseModel):
    """Payload to confirm a booking from an active reservation."""

    reservation_id: str = Field(description="Active reservation UUID")
    notes: str | None = Field(default=None, max_length=1000, description="Optional client notes for therapist")


class CancelBookingRequest(BaseModel):
    """Payload to cancel an existing consultation booking."""

    reason: str | None = Field(default=None, max_length=500, description="Reason for cancellation")


class BookingSummaryResponse(BaseModel):
    """Summary booking response for listings and dashboards."""

    id: str
    client_id: str
    therapist_id: str
    session_mode: SessionMode
    start_at: datetime
    end_at: datetime
    duration_minutes: int
    status: BookingStatus
    pricing: PricingSnapshot
    therapist: TherapistSnapshot
    created_at: datetime
    session_id: str | None = None
    meeting: BookingMeetingResponse | None = None

    @classmethod
    def from_db(
        cls,
        doc: BookingInDB,
        session_id: str | None = None,
        meeting: BookingMeetingResponse | None = None,
    ) -> "BookingSummaryResponse":
        return cls(
            id=doc.id,
            client_id=doc.client_id,
            therapist_id=doc.therapist_id,
            session_mode=doc.session_mode,
            start_at=doc.start_at,
            end_at=doc.end_at,
            duration_minutes=doc.duration_minutes,
            status=doc.status,
            pricing=doc.pricing,
            therapist=doc.therapist,
            created_at=doc.created_at,
            session_id=session_id,
            meeting=meeting,
        )


class BookingDetailResponse(BaseModel):
    """Comprehensive booking response with all snapshots and notes."""

    id: str
    client_id: str
    therapist_id: str
    slot_id: str
    reservation_id: str
    session_mode: SessionMode
    start_at: datetime
    end_at: datetime
    duration_minutes: int
    status: BookingStatus
    pricing: PricingSnapshot
    therapist: TherapistSnapshot
    client: ClientSnapshot
    notes: str | None
    cancellation_reason: str | None
    cancelled_at: datetime | None
    created_at: datetime
    updated_at: datetime
    session_id: str | None = None
    meeting: BookingMeetingResponse | None = None

    @classmethod
    def from_db(
        cls,
        doc: BookingInDB,
        session_id: str | None = None,
        meeting: BookingMeetingResponse | None = None,
    ) -> "BookingDetailResponse":
        return cls(
            id=doc.id,
            client_id=doc.client_id,
            therapist_id=doc.therapist_id,
            slot_id=doc.slot_id,
            reservation_id=doc.reservation_id,
            session_mode=doc.session_mode,
            start_at=doc.start_at,
            end_at=doc.end_at,
            duration_minutes=doc.duration_minutes,
            status=doc.status,
            pricing=doc.pricing,
            therapist=doc.therapist,
            client=doc.client,
            notes=doc.notes,
            cancellation_reason=doc.cancellation_reason,
            cancelled_at=doc.cancelled_at,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
            session_id=session_id,
            meeting=meeting,
        )
