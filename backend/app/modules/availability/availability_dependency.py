"""FastAPI dependencies for Availability repository and service."""

from typing import Any

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database.mongodb import get_database
from app.modules.availability.availability_repository import AvailabilityRepository
from app.modules.availability.availability_service import AvailabilityService
from app.modules.therapist.therapist_dependency import get_therapist_repository
from app.modules.therapist.therapist_repository import TherapistRepository


def get_availability_repository(
    db: AsyncIOMotorDatabase[dict[str, Any]] = Depends(get_database),
) -> AvailabilityRepository:
    """Dependency injecting AvailabilityRepository."""
    return AvailabilityRepository(db)


def get_availability_service(
    availability_repo: AvailabilityRepository = Depends(get_availability_repository),
    therapist_repo: TherapistRepository = Depends(get_therapist_repository),
) -> AvailabilityService:
    """Dependency injecting AvailabilityService."""
    return AvailabilityService(
        availability_repo=availability_repo,
        therapist_repo=therapist_repo,
    )
