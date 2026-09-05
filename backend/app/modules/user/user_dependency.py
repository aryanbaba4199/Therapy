"""FastAPI dependencies for User repository and service."""

from typing import Any

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database.mongodb import get_database
from app.modules.user.user_repository import UserRepository
from app.modules.user.user_service import UserService


def get_user_repository(
    db: AsyncIOMotorDatabase[dict[str, Any]] = Depends(get_database),
) -> UserRepository:
    """Dependency returning configured UserRepository."""
    return UserRepository(db)


def get_user_service(
    user_repo: UserRepository = Depends(get_user_repository),
) -> UserService:
    """Dependency returning configured UserService."""
    return UserService(user_repo)
