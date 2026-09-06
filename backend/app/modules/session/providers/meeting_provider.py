"""Protocol and schemas for Meeting Provider abstraction."""

from datetime import datetime
from typing import Protocol

from pydantic import BaseModel, Field

from app.modules.session.session_constants import MeetingProviderType, MeetingStatus


class MeetingAttendee(BaseModel):
    """Sanitized attendee details for calendar event creation."""

    name: str
    email: str
    role: str = Field(description="'therapist' or 'client'")


class MeetingCreationRequest(BaseModel):
    """Strongly typed input payload to create a remote meeting/calendar event."""

    session_id: str
    title: str
    start_at: datetime
    end_at: datetime
    timezone: str = "Asia/Kolkata"
    attendees: list[MeetingAttendee]


class MeetingCreationResult(BaseModel):
    """Structured result returned by any MeetingProvider implementation."""

    provider: MeetingProviderType
    status: MeetingStatus
    join_url: str | None = None
    provider_event_id: str | None = None
    conference_id: str | None = None
    error_message: str | None = None


class MeetingProvider(Protocol):
    """Abstract interface defining the meeting provider contract."""

    @property
    def name(self) -> MeetingProviderType:
        """Provider name identifier."""
        ...

    async def create_meeting(self, req: MeetingCreationRequest) -> MeetingCreationResult:
        """Create a scheduled event with conference solution."""
        ...
