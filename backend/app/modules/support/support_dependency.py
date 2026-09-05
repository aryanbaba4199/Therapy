"""Dependency injection providers for Support module."""

from typing import Any

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database.mongodb import get_database
from app.modules.support.support_repository import SupportRepository
from app.modules.support.support_service import SupportService


def get_support_repository(
    db: AsyncIOMotorDatabase[dict[str, Any]] = Depends(get_database),
) -> SupportRepository:
    return SupportRepository(db=db)


def get_support_service(
    db: AsyncIOMotorDatabase[dict[str, Any]] = Depends(get_database),
    support_repo: SupportRepository = Depends(get_support_repository),
) -> SupportService:
    return SupportService(db=db, support_repo=support_repo)
