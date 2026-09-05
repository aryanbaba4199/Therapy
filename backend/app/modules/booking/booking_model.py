"""MongoDB document persistence models for Reservations and Bookings."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.common.utils.datetime_utils import ensure_utc, utc_now
from app.modules.booking.booking_constants import BookingStatus, ReservationStatus
from app.modules.therapist.therapist_constants import SessionMode


class PricingSnapshot(BaseModel):
    """Immutable pricing snapshot at time of booking."""

    amount: float = Field(ge=0, description="Consultation fee amount")
    currency: str = Field(default="INR", max_length=3, description="Currency code")
    duration_minutes: int = Field(ge=15, description="Consultation duration in minutes")


class TherapistSnapshot(BaseModel):
    """Immutable therapist profile snapshot for historical audit."""

    id: str
    display_name: str
    designation: str
    specialization: str
    profile_image_url: str | None = None


class ClientSnapshot(BaseModel):
    """Immutable client profile snapshot for historical audit."""

    id: str
    first_name: str
    last_name: str
    email: str | None = None
    phone: str | None = None


class ReservationInDB(BaseModel):
    """Temporary slot hold stored in MongoDB `reservations` collection."""

    id: str = Field(description="Unique reservation UUID")
    slot_id: str = Field(description="Unique deterministic slot identifier from Phase 4")
    therapist_id: str = Field(description="Therapist UUID")
    client_id: str = Field(description="Client user UUID")
    session_mode: SessionMode
    start_at: datetime = Field(description="Slot start time in UTC")
    end_at: datetime = Field(description="Slot end time in UTC")
    duration_minutes: int = Field(ge=15)
    status: ReservationStatus = Field(default=ReservationStatus.ACTIVE)
    reserved_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime = Field(description="UTC timestamp when reservation expires")
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("start_at", "end_at", "reserved_at", "expires_at", "created_at", "updated_at", mode="after")
    @classmethod
    def ensure_tz(cls, v: datetime | None) -> datetime | None:
        return ensure_utc(v) if v is not None else None

    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        d = super().model_dump(*args, **kwargs)
        for key in ["start_at", "end_at", "reserved_at", "expires_at", "created_at", "updated_at"]:
            if key in d and isinstance(d[key], datetime):
                d[key] = ensure_utc(d[key])
        return d


class BookingInDB(BaseModel):
    """Confirmed consultation booking stored in MongoDB `bookings` collection."""

    id: str = Field(description="Unique booking UUID")
    client_id: str = Field(description="Client user UUID")
    therapist_id: str = Field(description="Therapist UUID")
    slot_id: str = Field(description="Slot identifier")
    reservation_id: str = Field(description="Original reservation UUID")
    session_mode: SessionMode
    start_at: datetime = Field(description="Slot start time in UTC")
    end_at: datetime = Field(description="Slot end time in UTC")
    duration_minutes: int = Field(ge=15)
    status: BookingStatus = Field(default=BookingStatus.CONFIRMED)
    pricing: PricingSnapshot
    therapist: TherapistSnapshot
    client: ClientSnapshot
    notes: str | None = None
    cancellation_reason: str | None = None
    cancelled_at: datetime | None = None
    cancelled_by: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("start_at", "end_at", "cancelled_at", "created_at", "updated_at", mode="after")
    @classmethod
    def ensure_tz(cls, v: datetime | None) -> datetime | None:
        return ensure_utc(v) if v is not None else None

    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        d = super().model_dump(*args, **kwargs)
        for key in ["start_at", "end_at", "cancelled_at", "created_at", "updated_at"]:
            if key in d and isinstance(d[key], datetime):
                d[key] = ensure_utc(d[key])
        return d
