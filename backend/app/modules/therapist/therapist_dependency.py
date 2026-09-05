"""FastAPI dependencies for Therapist repository and service."""

from typing import Any

from fastapi import Depends, Header
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import Settings, get_settings
from app.database.mongodb import get_database
from app.modules.auth.auth_dependency import oauth2_scheme
from app.modules.auth.auth_utils import decode_jwt_token
from app.modules.therapist.therapist_repository import TherapistRepository
from app.modules.therapist.therapist_service import TherapistService
from app.modules.user.user_dependency import get_user_repository
from app.modules.user.user_model import UserInDB
from app.modules.user.user_repository import UserRepository


def get_therapist_repository(
    db: AsyncIOMotorDatabase[dict[str, Any]] = Depends(get_database),
) -> TherapistRepository:
    """Dependency injecting TherapistRepository."""
    return TherapistRepository(db)


def get_therapist_service(
    therapist_repo: TherapistRepository = Depends(get_therapist_repository),
    user_repo: UserRepository = Depends(get_user_repository),
) -> TherapistService:
    """Dependency injecting TherapistService."""
    return TherapistService(therapist_repo=therapist_repo, user_repo=user_repo)


async def get_optional_current_user(
    token: str | None = Depends(oauth2_scheme),
    auth_header: str | None = Header(None, alias="Authorization"),
    user_repo: UserRepository = Depends(get_user_repository),
    settings: Settings = Depends(get_settings),
) -> UserInDB | None:
    """Safely extract current user if authenticated, without raising on anonymous calls."""
    raw_token = token
    if not raw_token and auth_header and auth_header.startswith("Bearer "):
        raw_token = auth_header[7:].strip()

    if not raw_token:
        return None

    try:
        payload = decode_jwt_token(
            token=raw_token,
            secret_key=settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )
        user_id = payload.get("sub")
        if not user_id:
            return None
        return await user_repo.get_by_id(user_id)
    except Exception:
        return None
