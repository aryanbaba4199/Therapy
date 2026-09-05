"""Dependency injection for Package module."""

from typing import Any

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database.mongodb import get_database
from app.modules.package.package_repository import PackageRepository
from app.modules.package.package_service import PackageService


def get_package_repository(
    db: AsyncIOMotorDatabase[dict[str, Any]] = Depends(get_database),
) -> PackageRepository:
    return PackageRepository(db=db)


def get_package_service(
    package_repo: PackageRepository = Depends(get_package_repository),
) -> PackageService:
    return PackageService(package_repo=package_repo)
