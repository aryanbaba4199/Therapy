"""Domain entities and MongoDB database persistence models for Sessions."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.common.utils.datetime_utils import ensure_utc, utc_now
from app.modules.session.session_constants import AttendanceStatus, GoalStatus, SessionStatus


class SessionInDB(BaseModel):
    """Database model for a therapy session stored in `sessions` collection."""

    id: str = Field(description="Unique session UUID")
    booking_id: str = Field(description="Unique reference to confirmed booking")
    therapist_id: str = Field(description="Therapist profile UUID")
    client_id: str = Field(description="Client user UUID")

    scheduled_start_at: datetime = Field(description="Scheduled start timestamp in UTC")
    scheduled_end_at: datetime = Field(description="Scheduled end timestamp in UTC")
    duration_minutes: int = Field(ge=1, description="Duration in minutes")
    session_mode: str = Field(description="Session mode, e.g. online, offline_kozhikode")

    status: SessionStatus = Field(default=SessionStatus.SCHEDULED)
    started_at: datetime | None = Field(default=None, description="Actual start time in UTC")
    ended_at: datetime | None = Field(default=None, description="Actual completion time in UTC")

    attendance: AttendanceStatus = Field(default=AttendanceStatus.UNKNOWN)

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator(
        "scheduled_start_at",
        "scheduled_end_at",
        "started_at",
        "ended_at",
        "created_at",
        "updated_at",
        mode="after",
    )
    @classmethod
    def ensure_tz(cls, v: datetime | None) -> datetime | None:
        return ensure_utc(v) if v is not None else None

    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        d = super().model_dump(*args, **kwargs)
        for key in [
            "scheduled_start_at",
            "scheduled_end_at",
            "started_at",
            "ended_at",
            "created_at",
            "updated_at",
        ]:
            if key in d and isinstance(d[key], datetime):
                d[key] = ensure_utc(d[key])
        return d


class SessionNoteInDB(BaseModel):
    """Clinical notes stored in dedicated `session_notes` collection."""

    id: str = Field(description="Unique session note UUID")
    session_id: str = Field(description="Session UUID reference")
    therapist_id: str = Field(description="Therapist UUID")
    client_id: str = Field(description="Client UUID")

    summary: str = Field(default="", description="High-level session summary")
    private_notes: str = Field(default="", description="Therapist-only confidential clinical notes")

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


class TherapyGoalInDB(BaseModel):
    """Client therapy goal stored in dedicated `therapy_goals` collection."""

    id: str = Field(description="Unique goal UUID")
    session_id: str | None = Field(default=None, description="Optional originating session UUID")
    therapist_id: str = Field(description="Therapist UUID")
    client_id: str = Field(description="Client UUID")

    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    status: GoalStatus = Field(default=GoalStatus.ACTIVE)

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
