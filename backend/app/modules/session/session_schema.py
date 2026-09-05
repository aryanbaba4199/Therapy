"""Pydantic request and response schemas for Session and Clinical domain."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.session.session_constants import AttendanceStatus, GoalStatus, SessionStatus
from app.modules.session.session_model import SessionInDB, SessionNoteInDB, TherapyGoalInDB

# --- Session Schemas ---

class SessionResponse(BaseModel):
    """Full session representation for assigned therapist."""

    id: str
    booking_id: str
    therapist_id: str
    client_id: str
    scheduled_start_at: datetime
    scheduled_end_at: datetime
    duration_minutes: int
    session_mode: str
    status: SessionStatus
    started_at: datetime | None = None
    ended_at: datetime | None = None
    attendance: AttendanceStatus
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_db(cls, doc: SessionInDB) -> "SessionResponse":
        return cls(
            id=doc.id,
            booking_id=doc.booking_id,
            therapist_id=doc.therapist_id,
            client_id=doc.client_id,
            scheduled_start_at=doc.scheduled_start_at,
            scheduled_end_at=doc.scheduled_end_at,
            duration_minutes=doc.duration_minutes,
            session_mode=doc.session_mode,
            status=doc.status,
            started_at=doc.started_at,
            ended_at=doc.ended_at,
            attendance=doc.attendance,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )


class ClientSessionResponse(BaseModel):
    """Sanitized session representation for clients (never exposes clinical internals)."""

    id: str
    booking_id: str
    therapist_id: str
    scheduled_start_at: datetime
    scheduled_end_at: datetime
    duration_minutes: int
    session_mode: str
    status: SessionStatus
    started_at: datetime | None = None
    ended_at: datetime | None = None

    @classmethod
    def from_db(cls, doc: SessionInDB) -> "ClientSessionResponse":
        return cls(
            id=doc.id,
            booking_id=doc.booking_id,
            therapist_id=doc.therapist_id,
            scheduled_start_at=doc.scheduled_start_at,
            scheduled_end_at=doc.scheduled_end_at,
            duration_minutes=doc.duration_minutes,
            session_mode=doc.session_mode,
            status=doc.status,
            started_at=doc.started_at,
            ended_at=doc.ended_at,
        )


class RecordAttendanceRequest(BaseModel):
    """Payload to record client session attendance."""

    attendance: AttendanceStatus


# --- Clinical Notes Schemas ---

class UpsertSessionNoteRequest(BaseModel):
    """Therapist payload to update clinical notes."""

    summary: str = Field(default="", max_length=5000)
    private_notes: str = Field(default="", max_length=10000)


class SessionNoteResponse(BaseModel):
    """Full note representation accessible ONLY to authorized therapist."""

    id: str
    session_id: str
    therapist_id: str
    client_id: str
    summary: str
    private_notes: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_db(cls, doc: SessionNoteInDB) -> "SessionNoteResponse":
        return cls(
            id=doc.id,
            session_id=doc.session_id,
            therapist_id=doc.therapist_id,
            client_id=doc.client_id,
            summary=doc.summary,
            private_notes=doc.private_notes,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )


class ClientSessionNoteResponse(BaseModel):
    """Client-accessible note representation (strictly summary only, ZERO private notes)."""

    session_id: str
    summary: str
    updated_at: datetime

    @classmethod
    def from_db(cls, doc: SessionNoteInDB) -> "ClientSessionNoteResponse":
        return cls(
            session_id=doc.session_id,
            summary=doc.summary,
            updated_at=doc.updated_at,
        )


# --- Therapy Goals Schemas ---

class CreateTherapyGoalRequest(BaseModel):
    """Payload to create a new client therapy goal."""

    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)


class UpdateTherapyGoalRequest(BaseModel):
    """Payload to update an existing goal."""

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    status: GoalStatus | None = None


class TherapyGoalResponse(BaseModel):
    """Therapy goal response."""

    id: str
    session_id: str | None
    therapist_id: str
    client_id: str
    title: str
    description: str
    status: GoalStatus
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_db(cls, doc: TherapyGoalInDB) -> "TherapyGoalResponse":
        return cls(
            id=doc.id,
            session_id=doc.session_id,
            therapist_id=doc.therapist_id,
            client_id=doc.client_id,
            title=doc.title,
            description=doc.description,
            status=doc.status,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )


# --- Therapist Dashboard Schemas ---

class TherapistDashboardSummaryResponse(BaseModel):
    """Aggregated operational stats for therapist dashboard."""

    today_sessions_count: int
    upcoming_sessions_count: int
    completed_sessions_count: int
    today_sessions: list[SessionResponse]
