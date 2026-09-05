"""Request and response schemas for the Therapist API."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.modules.therapist.therapist_constants import (
    SessionMode,
    TherapistSpecialization,
    TherapistStatus,
    TherapistVerificationStatus,
)
from app.modules.therapist.therapist_model import TherapistInDB


class TherapistPricingSchema(BaseModel):
    """Session pricing structure."""

    amount: float = Field(ge=0, description="Consultation fee")
    currency: str = Field(default="INR", max_length=3, description="Currency code")
    duration_minutes: int = Field(
        default=60, ge=15, le=180, description="Consultation duration in minutes"
    )


class TherapistVerificationSchema(BaseModel):
    """Public verification details."""

    status: TherapistVerificationStatus
    verified_at: datetime | None = None
    rejection_reason: str | None = None


class TherapistSummaryResponse(BaseModel):
    """Public lightweight representation for discovery cards."""

    id: str
    display_name: str
    designation: str
    specialization: TherapistSpecialization
    experience_years: int
    therapy_hours: int
    languages: list[str]
    expertises: list[str]
    session_modes: list[SessionMode]
    pricing: TherapistPricingSchema
    profile_image_url: str | None = None
    is_verified: bool
    status: TherapistStatus

    @classmethod
    def from_therapist_db(cls, doc: TherapistInDB) -> "TherapistSummaryResponse":
        """Convert database entity to public summary schema."""
        return cls(
            id=doc.id,
            display_name=doc.display_name,
            designation=doc.designation,
            specialization=doc.specialization,
            experience_years=doc.experience_years,
            therapy_hours=doc.therapy_hours,
            languages=doc.languages,
            expertises=doc.expertises,
            session_modes=doc.session_modes,
            pricing=TherapistPricingSchema(
                amount=doc.pricing.amount,
                currency=doc.pricing.currency,
                duration_minutes=doc.pricing.duration_minutes,
            ),
            profile_image_url=doc.profile_image_url,
            is_verified=doc.verification.status == TherapistVerificationStatus.VERIFIED,
            status=doc.status,
        )


class TherapistDetailResponse(BaseModel):
    """Comprehensive representation for therapist profile page."""

    id: str
    user_id: str
    first_name: str
    last_name: str
    display_name: str
    bio: str
    profile_image_url: str | None = None
    introduction_audio_url: str | None = None
    designation: str
    specialization: TherapistSpecialization
    qualifications: list[str]
    experience_years: int
    therapy_hours: int
    languages: list[str]
    expertises: list[str]
    session_modes: list[SessionMode]
    pricing: TherapistPricingSchema
    verification: TherapistVerificationSchema
    status: TherapistStatus
    created_at: datetime

    @classmethod
    def from_therapist_db(cls, doc: TherapistInDB) -> "TherapistDetailResponse":
        """Convert database entity to detailed profile schema."""
        return cls(
            id=doc.id,
            user_id=doc.user_id,
            first_name=doc.first_name,
            last_name=doc.last_name,
            display_name=doc.display_name,
            bio=doc.bio,
            profile_image_url=doc.profile_image_url,
            introduction_audio_url=doc.introduction_audio_url,
            designation=doc.designation,
            specialization=doc.specialization,
            qualifications=doc.qualifications,
            experience_years=doc.experience_years,
            therapy_hours=doc.therapy_hours,
            languages=doc.languages,
            expertises=doc.expertises,
            session_modes=doc.session_modes,
            pricing=TherapistPricingSchema(
                amount=doc.pricing.amount,
                currency=doc.pricing.currency,
                duration_minutes=doc.pricing.duration_minutes,
            ),
            verification=TherapistVerificationSchema(
                status=doc.verification.status,
                verified_at=doc.verification.verified_at,
                rejection_reason=doc.verification.rejection_reason,
            ),
            status=doc.status,
            created_at=doc.created_at,
        )


class CreateTherapistRequest(BaseModel):
    """Payload to create a therapist profile."""

    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    display_name: str | None = Field(default=None, max_length=100)
    bio: str = Field(min_length=10, max_length=5000)
    designation: str = Field(min_length=2, max_length=100)
    specialization: TherapistSpecialization
    qualifications: list[str] = Field(min_length=1)
    experience_years: int = Field(ge=0, le=70)
    therapy_hours: int = Field(default=0, ge=0)
    languages: list[str] = Field(min_length=1)
    expertises: list[str] = Field(min_length=1)
    session_modes: list[SessionMode] = Field(min_length=1)
    pricing: TherapistPricingSchema
    profile_image_url: str | None = None
    introduction_audio_url: str | None = None

    @field_validator("languages", mode="after")
    @classmethod
    def clean_languages(cls, v: list[str]) -> list[str]:
        cleaned = [lang.strip().lower() for lang in v if lang.strip()]
        if not cleaned:
            raise ValueError("At least one language must be specified")
        return cleaned

    @field_validator("expertises", mode="after")
    @classmethod
    def clean_expertises(cls, v: list[str]) -> list[str]:
        cleaned = [exp.strip().lower() for exp in v if exp.strip()]
        if not cleaned:
            raise ValueError("At least one area of expertise must be specified")
        return cleaned


class UpdateTherapistRequest(BaseModel):
    """Self-service update payload for a therapist profile."""

    display_name: str | None = Field(default=None, max_length=100)
    bio: str | None = Field(default=None, min_length=10, max_length=5000)
    designation: str | None = Field(default=None, min_length=2, max_length=100)
    specialization: TherapistSpecialization | None = None
    qualifications: list[str] | None = None
    experience_years: int | None = Field(default=None, ge=0, le=70)
    therapy_hours: int | None = Field(default=None, ge=0)
    languages: list[str] | None = None
    expertises: list[str] | None = None
    session_modes: list[SessionMode] | None = None
    pricing: TherapistPricingSchema | None = None
    profile_image_url: str | None = None
    introduction_audio_url: str | None = None
    status: TherapistStatus | None = None


class AdminUpdateTherapistVerificationRequest(BaseModel):
    """Privileged verification status update."""

    status: TherapistVerificationStatus
    rejection_reason: str | None = None
