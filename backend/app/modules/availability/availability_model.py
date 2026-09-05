"""MongoDB document persistence models for Availability."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.common.utils.datetime_utils import ensure_utc, utc_now
from app.modules.availability.availability_constants import (
    DEFAULT_TIMEZONE,
    DayOfWeek,
    SlotStatus,
)
from app.modules.therapist.therapist_constants import SessionMode


class DayInterval(BaseModel):
    """Working hours interval on a recurring day or exception date."""

    start_time: str = Field(description="Start time in HH:MM 24-hour format")
    end_time: str = Field(description="End time in HH:MM 24-hour format")
    session_modes: list[SessionMode] = Field(
        default_factory=lambda: [SessionMode.ONLINE],
        description="Delivery modes available in this window",
    )


class DaySchedule(BaseModel):
    """Configuration for a specific day of the week."""

    day_of_week: DayOfWeek
    intervals: list[DayInterval] = Field(default_factory=list)


class WeeklyScheduleInDB(BaseModel):
    """Recurring weekly schedule stored in `availability_schedules` collection."""

    id: str = Field(description="Unique schedule UUID")
    therapist_id: str = Field(description="Associated therapist UUID")
    timezone: str = Field(default=DEFAULT_TIMEZONE, description="IANA timezone name")
    days: list[DaySchedule] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("created_at", "updated_at", mode="after")
    @classmethod
    def ensure_tz(cls, v: datetime) -> datetime:
        return ensure_utc(v)

    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        d = super().model_dump(*args, **kwargs)
        if "created_at" in d and isinstance(d["created_at"], datetime):
            d["created_at"] = ensure_utc(d["created_at"])
        if "updated_at" in d and isinstance(d["updated_at"], datetime):
            d["updated_at"] = ensure_utc(d["updated_at"])
        return d


class DateExceptionInDB(BaseModel):
    """Date-specific override or holiday stored in `availability_exceptions` collection."""

    id: str = Field(description="Unique exception UUID")
    therapist_id: str = Field(description="Associated therapist UUID")
    date: str = Field(description="Target ISO date (YYYY-MM-DD)")
    is_unavailable: bool = Field(
        default=True, description="Whether the entire day is unavailable"
    )
    custom_intervals: list[DayInterval] = Field(
        default_factory=list, description="Custom working intervals overriding recurring rules"
    )
    reason: str | None = Field(default=None, description="Optional note (e.g. Leave, Conference)")
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("created_at", "updated_at", mode="after")
    @classmethod
    def ensure_tz(cls, v: datetime) -> datetime:
        return ensure_utc(v)


class ExtraSlotInDB(BaseModel):
    """One-off extra slot stored in `extra_slots` collection."""

    id: str = Field(description="Unique extra slot UUID")
    therapist_id: str = Field(description="Associated therapist UUID")
    date: str = Field(description="Target ISO date (YYYY-MM-DD)")
    start_time: str = Field(description="Start time in HH:MM")
    end_time: str = Field(description="End time in HH:MM")
    session_mode: SessionMode = Field(default=SessionMode.ONLINE)
    status: SlotStatus = Field(default=SlotStatus.AVAILABLE)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("created_at", "updated_at", mode="after")
    @classmethod
    def ensure_tz(cls, v: datetime) -> datetime:
        return ensure_utc(v)
