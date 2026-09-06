"""Dependency injection providers for Session module."""

from typing import Any

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import Settings, get_settings
from app.database.mongodb import get_database
from app.modules.booking.booking_dependency import get_booking_repository
from app.modules.booking.booking_repository import BookingRepository
from app.modules.session.providers.google_meet_provider import GoogleMeetProvider
from app.modules.session.providers.meeting_provider import MeetingProvider
from app.modules.session.providers.mock_meeting_provider import MockMeetingProvider
from app.modules.session.session_repository import SessionRepository
from app.modules.session.session_service import SessionService
from app.modules.therapist.therapist_dependency import get_therapist_repository
from app.modules.therapist.therapist_repository import TherapistRepository


def get_meeting_provider(settings: Settings = Depends(get_settings)) -> MeetingProvider:
    """Provide configured meeting provider based on settings."""
    if settings.google_calendar_enabled:
        return GoogleMeetProvider(
            service_account_email=settings.google_service_account_email,
            private_key=settings.google_service_account_private_key,
            calendar_id=settings.google_calendar_id,
            delegated_user=settings.google_calendar_delegated_user,
        )
    return MockMeetingProvider()


def get_session_repository(
    db: AsyncIOMotorDatabase[dict[str, Any]] = Depends(get_database),
) -> SessionRepository:
    return SessionRepository(db=db)


def get_session_service(
    session_repo: SessionRepository = Depends(get_session_repository),
    booking_repo: BookingRepository = Depends(get_booking_repository),
    therapist_repo: TherapistRepository = Depends(get_therapist_repository),
    settings: Settings = Depends(get_settings),
    meeting_provider: MeetingProvider = Depends(get_meeting_provider),
) -> SessionService:
    return SessionService(
        session_repo=session_repo,
        booking_repo=booking_repo,
        therapist_repo=therapist_repo,
        settings=settings,
        meeting_provider=meeting_provider,
    )
