"""Dependency injection providers for Session module."""

from typing import Any

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import Settings, get_settings
from app.database.mongodb import get_database
from app.modules.booking.booking_dependency import get_booking_repository
from app.modules.booking.booking_repository import BookingRepository
from app.modules.session.session_repository import SessionRepository
from app.modules.session.session_service import SessionService
from app.modules.therapist.therapist_dependency import get_therapist_repository
from app.modules.therapist.therapist_repository import TherapistRepository


def get_session_repository(
    db: AsyncIOMotorDatabase[dict[str, Any]] = Depends(get_database),
) -> SessionRepository:
    return SessionRepository(db=db)


def get_session_service(
    session_repo: SessionRepository = Depends(get_session_repository),
    booking_repo: BookingRepository = Depends(get_booking_repository),
    therapist_repo: TherapistRepository = Depends(get_therapist_repository),
    settings: Settings = Depends(get_settings),
) -> SessionService:
    return SessionService(
        session_repo=session_repo,
        booking_repo=booking_repo,
        therapist_repo=therapist_repo,
        settings=settings,
    )
