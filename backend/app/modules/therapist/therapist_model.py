"""MongoDB document persistence model for Therapists."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.common.utils.datetime_utils import ensure_utc, utc_now
from app.modules.therapist.therapist_constants import (
    SessionMode,
    TherapistSpecialization,
    TherapistStatus,
    TherapistVerificationStatus,
)


class PricingModel(BaseModel):
    """Consultation fee structure."""

    amount: float = Field(ge=0, description="Session fee amount")
    currency: str = Field(default="INR", max_length=3, description="ISO currency code")
    duration_minutes: int = Field(
        default=60, ge=15, le=180, description="Session duration in minutes"
    )


class VerificationModel(BaseModel):
    """Administrative verification audit details."""

    status: TherapistVerificationStatus = Field(default=TherapistVerificationStatus.PENDING)
    verified_at: datetime | None = None
    verified_by: str | None = Field(default=None, description="Admin/Staff user UUID")
    rejection_reason: str | None = None

    @field_validator("verified_at", mode="after")
    @classmethod
    def make_tz_aware(cls, v: datetime | None) -> datetime | None:
        return ensure_utc(v) if v is not None else None


class TherapistInDB(BaseModel):
    """Therapist representation stored in MongoDB collection `therapists`."""

    id: str = Field(description="Unique therapist UUID")
    user_id: str = Field(description="Associated authenticated user UUID")
    first_name: str
    last_name: str
    display_name: str
    bio: str
    profile_image_url: str | None = None
    introduction_audio_url: str | None = None
    designation: str
    specialization: TherapistSpecialization
    qualifications: list[str] = Field(default_factory=list)
    experience_years: int = Field(default=0, ge=0)
    therapy_hours: int = Field(default=0, ge=0)
    languages: list[str] = Field(default_factory=lambda: ["en"])
    expertises: list[str] = Field(default_factory=list)
    session_modes: list[SessionMode] = Field(default_factory=lambda: [SessionMode.ONLINE])
    pricing: PricingModel
    verification: VerificationModel = Field(default_factory=VerificationModel)
    status: TherapistStatus = Field(default=TherapistStatus.DRAFT)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("created_at", "updated_at", mode="after")
    @classmethod
    def make_tz_aware(cls, v: datetime | None) -> datetime | None:
        return ensure_utc(v) if v is not None else None
