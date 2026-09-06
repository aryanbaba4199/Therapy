"""Pydantic request and response schemas for Review domain."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.review.review_constants import ReviewStatus
from app.modules.review.review_model import ReviewInDB


class CreateReviewRequest(BaseModel):
    """Payload to submit a post-session therapist review."""

    session_id: str = Field(description="UUID of completed therapy session")
    rating: int = Field(ge=1, le=5, description="Rating from 1 to 5 stars")
    comment: str = Field(default="", max_length=2000, description="Optional written review feedback")
    is_anonymous: bool = Field(default=False, description="Whether to display name anonymously")


class ReviewResponse(BaseModel):
    """Full review representation for client history and staff."""

    id: str
    session_id: str
    booking_id: str
    therapist_id: str
    client_id: str
    rating: int
    comment: str
    client_display_name: str
    is_anonymous: bool
    status: ReviewStatus
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_db(cls, doc: ReviewInDB) -> "ReviewResponse":
        display_name = "Anonymous Client" if doc.is_anonymous else doc.client_display_name
        return cls(
            id=doc.id,
            session_id=doc.session_id,
            booking_id=doc.booking_id,
            therapist_id=doc.therapist_id,
            client_id=doc.client_id,
            rating=doc.rating,
            comment=doc.comment,
            client_display_name=display_name,
            is_anonymous=doc.is_anonymous,
            status=doc.status,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )


class PublicReviewResponse(BaseModel):
    """Sanitized public review representation displayed on therapist profile."""

    id: str
    therapist_id: str
    rating: int
    comment: str
    client_display_name: str
    created_at: datetime

    @classmethod
    def from_db(cls, doc: ReviewInDB) -> "PublicReviewResponse":
        display_name = "Anonymous Client" if doc.is_anonymous else doc.client_display_name
        return cls(
            id=doc.id,
            therapist_id=doc.therapist_id,
            rating=doc.rating,
            comment=doc.comment,
            client_display_name=display_name,
            created_at=doc.created_at,
        )


class TherapistRatingSummaryResponse(BaseModel):
    """Aggregate rating metrics for a therapist profile."""

    therapist_id: str
    average_rating: float = Field(ge=0.0, le=5.0)
    review_count: int = Field(ge=0)
    distribution: dict[str, int] = Field(
        default_factory=lambda: {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
    )


class ModerateReviewRequest(BaseModel):
    """Staff payload to update review moderation status."""

    status: ReviewStatus
