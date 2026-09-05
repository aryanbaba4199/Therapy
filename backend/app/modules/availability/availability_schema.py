"""Pydantic v2 schemas for Availability request validation and responses."""

import re
from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, field_validator, model_validator

from app.modules.availability.availability_constants import (
    DEFAULT_TIMEZONE,
    DayOfWeek,
    SlotStatus,
)
from app.modules.availability.availability_model import (
    DateExceptionInDB,
    ExtraSlotInDB,
    WeeklyScheduleInDB,
)
from app.modules.therapist.therapist_constants import SessionMode

TIME_REGEX = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")
DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class TimeIntervalSchema(BaseModel):
    """Start and end time boundaries with allowed session delivery modes."""

    start_time: str = Field(description="Start time (HH:MM in 24-hour format)")
    end_time: str = Field(description="End time (HH:MM in 24-hour format)")
    session_modes: list[SessionMode] = Field(
        default_factory=lambda: [SessionMode.ONLINE],
        min_length=1,
        description="Delivery modes available in this interval",
    )

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        if not TIME_REGEX.match(v):
            raise ValueError("Time must be in HH:MM format (00:00 - 23:59)")
        return v

    @model_validator(mode="after")
    def validate_interval_order(self) -> "TimeIntervalSchema":
        if self.start_time >= self.end_time:
            raise ValueError(f"start_time ({self.start_time}) must be earlier than end_time ({self.end_time})")
        return self


class DayScheduleSchema(BaseModel):
    """Day schedule with working intervals."""

    day_of_week: DayOfWeek
    intervals: list[TimeIntervalSchema] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_non_overlapping_intervals(self) -> "DayScheduleSchema":
        """Verify that no intervals on the same day overlap for the same session mode."""
        sorted_intervals = sorted(self.intervals, key=lambda x: x.start_time)
        for i in range(len(sorted_intervals) - 1):
            curr = sorted_intervals[i]
            next_int = sorted_intervals[i + 1]
            if curr.end_time > next_int.start_time:
                # Check if there is an overlapping session mode
                shared_modes = set(curr.session_modes).intersection(set(next_int.session_modes))
                if shared_modes:
                    mode_names = ", ".join(m.value for m in shared_modes)
                    raise ValueError(
                        f"Overlapping intervals on day {self.day_of_week}: "
                        f"{curr.start_time}-{curr.end_time} and {next_int.start_time}-{next_int.end_time} "
                        f"for modes ({mode_names})"
                    )
        return self


class SetWeeklyScheduleRequest(BaseModel):
    """Payload to create or replace a therapist's weekly recurring schedule."""

    timezone: str = Field(default=DEFAULT_TIMEZONE, description="IANA timezone name")
    days: list[DayScheduleSchema] = Field(default_factory=list)

    @field_validator("timezone")
    @classmethod
    def validate_timezone(cls, v: str) -> str:
        try:
            ZoneInfo(v)
        except Exception as exc:
            raise ValueError(f"Invalid IANA timezone: '{v}'") from exc
        return v



class WeeklyScheduleResponse(BaseModel):
    """Therapist's weekly schedule response."""

    id: str
    therapist_id: str
    timezone: str
    days: list[DayScheduleSchema]
    updated_at: datetime

    @classmethod
    def from_db(cls, doc: WeeklyScheduleInDB) -> "WeeklyScheduleResponse":
        return cls(
            id=doc.id,
            therapist_id=doc.therapist_id,
            timezone=doc.timezone,
            days=[
                DayScheduleSchema(
                    day_of_week=d.day_of_week,
                    intervals=[
                        TimeIntervalSchema(
                            start_time=i.start_time,
                            end_time=i.end_time,
                            session_modes=i.session_modes,
                        )
                        for i in d.intervals
                    ],
                )
                for d in doc.days
            ],
            updated_at=doc.updated_at,
        )


class CreateDateExceptionRequest(BaseModel):
    """Payload to add or replace an exception for a specific date."""

    date: str = Field(description="Target date in YYYY-MM-DD format")
    is_unavailable: bool = Field(default=True, description="Whether the entire day is unavailable")
    custom_intervals: list[TimeIntervalSchema] = Field(
        default_factory=list, description="Custom intervals if not completely unavailable"
    )
    reason: str | None = Field(default=None, max_length=200, description="Reason note")

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        if not DATE_REGEX.match(v):
            raise ValueError("Date must be in YYYY-MM-DD format")
        return v

    @model_validator(mode="after")
    def validate_exception_logic(self) -> "CreateDateExceptionRequest":
        if not self.is_unavailable and not self.custom_intervals:
            raise ValueError("If is_unavailable is False, at least one custom interval must be provided")
        return self


class DateExceptionResponse(BaseModel):
    """Specific date exception response."""

    id: str
    therapist_id: str
    date: str
    is_unavailable: bool
    custom_intervals: list[TimeIntervalSchema]
    reason: str | None
    created_at: datetime

    @classmethod
    def from_db(cls, doc: DateExceptionInDB) -> "DateExceptionResponse":
        return cls(
            id=doc.id,
            therapist_id=doc.therapist_id,
            date=doc.date,
            is_unavailable=doc.is_unavailable,
            custom_intervals=[
                TimeIntervalSchema(
                    start_time=i.start_time,
                    end_time=i.end_time,
                    session_modes=i.session_modes,
                )
                for i in doc.custom_intervals
            ],
            reason=doc.reason,
            created_at=doc.created_at,
        )


class CreateExtraSlotRequest(BaseModel):
    """Payload to create an extra consultation slot."""

    date: str = Field(description="Target date in YYYY-MM-DD format")
    start_time: str = Field(description="Start time (HH:MM)")
    end_time: str = Field(description="End time (HH:MM)")
    session_mode: SessionMode = Field(default=SessionMode.ONLINE)

    @field_validator("date")
    @classmethod
    def validate_date(cls, v: str) -> str:
        if not DATE_REGEX.match(v):
            raise ValueError("Date must be in YYYY-MM-DD format")
        return v

    @field_validator("start_time", "end_time")
    @classmethod
    def validate_time(cls, v: str) -> str:
        if not TIME_REGEX.match(v):
            raise ValueError("Time must be in HH:MM format")
        return v

    @model_validator(mode="after")
    def validate_slot_order(self) -> "CreateExtraSlotRequest":
        if self.start_time >= self.end_time:
            raise ValueError(f"start_time ({self.start_time}) must be earlier than end_time ({self.end_time})")
        return self


class ExtraSlotResponse(BaseModel):
    """Extra slot response."""

    id: str
    therapist_id: str
    date: str
    start_time: str
    end_time: str
    session_mode: SessionMode
    status: SlotStatus

    @classmethod
    def from_db(cls, doc: ExtraSlotInDB) -> "ExtraSlotResponse":
        return cls(
            id=doc.id,
            therapist_id=doc.therapist_id,
            date=doc.date,
            start_time=doc.start_time,
            end_time=doc.end_time,
            session_mode=doc.session_mode,
            status=doc.status,
        )


class GeneratedSlotResponse(BaseModel):
    """Canonical representation of an available consultation slot."""

    id: str = Field(description="Deterministic slot identifier")
    therapist_id: str
    start_at: datetime = Field(description="ISO 8601 UTC slot start timestamp")
    end_at: datetime = Field(description="ISO 8601 UTC slot end timestamp")
    session_mode: SessionMode
    status: SlotStatus = Field(default=SlotStatus.AVAILABLE)


class TherapistAvailabilityResponse(BaseModel):
    """Composite availability response containing weekly schedule and upcoming exceptions."""

    therapist_id: str
    timezone: str
    schedule: WeeklyScheduleResponse | None
    exceptions: list[DateExceptionResponse]
