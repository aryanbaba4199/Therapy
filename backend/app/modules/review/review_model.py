"""MongoDB database persistence model for Reviews and Feedback."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.common.utils.datetime_utils import ensure_utc, utc_now
from app.modules.review.review_constants import ReviewStatus


class ReviewInDB(BaseModel):
    """Database model for a session review stored in `reviews` collection."""

    id: str = Field(description="Unique review UUID")
    session_id: str = Field(description="Unique reference to completed session")
    booking_id: str = Field(description="Reference to booking")
    therapist_id: str = Field(description="Therapist profile UUID")
    client_id: str = Field(description="Client user UUID")

    rating: int = Field(ge=1, le=5, description="Client numerical rating (1 to 5 stars)")
    comment: str = Field(default="", max_length=2000, description="Optional written review feedback")
    client_display_name: str = Field(default="Anonymous Client", description="Sanitized display name for privacy")
    is_anonymous: bool = Field(default=False, description="Whether client requested anonymity")

    status: ReviewStatus = Field(default=ReviewStatus.PUBLISHED, description="Moderation status")

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("created_at", "updated_at", mode="after")
    @classmethod
    def ensure_tz(cls, v: datetime | None) -> datetime | None:
        return ensure_utc(v) if v is not None else None

    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        d = super().model_dump(*args, **kwargs)
        for key in ["created_at", "updated_at"]:
            if key in d and isinstance(d[key], datetime):
                d[key] = ensure_utc(d[key])
        return d
