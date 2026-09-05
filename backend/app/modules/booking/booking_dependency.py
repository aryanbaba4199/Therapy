"""FastAPI dependency injection factories for Booking and Reservation services."""

from typing import Any

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import Settings, get_settings
from app.database.mongodb import get_database
from app.modules.availability.availability_dependency import get_availability_service
from app.modules.availability.availability_service import AvailabilityService
from app.modules.booking.booking_repository import BookingRepository
from app.modules.booking.booking_service import BookingService
from app.modules.therapist.therapist_dependency import get_therapist_repository
from app.modules.therapist.therapist_repository import TherapistRepository


def get_booking_repository(
    db: AsyncIOMotorDatabase[dict[str, Any]] = Depends(get_database),
) -> BookingRepository:
    """Dependency injecting BookingRepository."""
    return BookingRepository(db)


def get_booking_service(
    booking_repo: BookingRepository = Depends(get_booking_repository),
    therapist_repo: TherapistRepository = Depends(get_therapist_repository),
    availability_service: AvailabilityService = Depends(get_availability_service),
    settings: Settings = Depends(get_settings),
) -> BookingService:
    """Dependency injecting configured BookingService."""
    return BookingService(
        booking_repo=booking_repo,
        therapist_repo=therapist_repo,
        availability_service=availability_service,
        settings=settings,
    )
