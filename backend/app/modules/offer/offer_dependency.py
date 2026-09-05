"""Dependency injection for Offer module."""

from typing import Any

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database.mongodb import get_database
from app.modules.offer.offer_repository import OfferRepository
from app.modules.offer.offer_service import OfferService


def get_offer_repository(
    db: AsyncIOMotorDatabase[dict[str, Any]] = Depends(get_database),
) -> OfferRepository:
    return OfferRepository(db=db)


def get_offer_service(
    offer_repo: OfferRepository = Depends(get_offer_repository),
) -> OfferService:
    return OfferService(offer_repo=offer_repo)
