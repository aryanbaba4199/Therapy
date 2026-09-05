"""MongoDB repository for Offers and Coupon management."""

from datetime import UTC, datetime
from typing import Any

from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo import ASCENDING, IndexModel

from app.modules.offer.offer_model import OfferInDB


class OfferRepository:
    """Repository accessing `offers` collection."""

    def __init__(self, db: AsyncIOMotorDatabase[dict[str, Any]]) -> None:
        self.db = db
        self.offers: AsyncIOMotorCollection[dict[str, Any]] = db["offers"]

    async def ensure_indexes(self) -> None:
        """Create indexes for fast lookup and unique coupon codes."""
        await self.offers.create_indexes([
            IndexModel([("code", ASCENDING)], unique=True, name="idx_offer_code_unique"),
            IndexModel(
                [("is_active", ASCENDING), ("valid_from", ASCENDING), ("valid_until", ASCENDING)],
                name="idx_offer_validity",
            ),
        ])

    async def create_offer(self, offer: OfferInDB) -> OfferInDB:
        """Insert a new offer document."""
        await self.offers.insert_one(offer.model_dump())
        return offer

    async def get_by_code(self, code: str) -> OfferInDB | None:
        """Find offer by coupon code (case-insensitive search via normalized uppercase)."""
        doc = await self.offers.find_one({"code": code.upper().strip()})
        return OfferInDB(**doc) if doc else None

    async def get_by_id(self, offer_id: str) -> OfferInDB | None:
        """Find offer by ID."""
        doc = await self.offers.find_one({"id": offer_id})
        return OfferInDB(**doc) if doc else None

    async def list_active_offers(self) -> list[OfferInDB]:
        """Fetch all currently active offers."""
        now = datetime.now(UTC)
        cursor = self.offers.find({
            "is_active": True,
            "valid_from": {"$lte": now},
            "valid_until": {"$gte": now},
        }).sort("created_at", -1)
        docs = await cursor.to_list(length=100)
        return [OfferInDB(**d) for d in docs]

    async def increment_usage_atomic(
        self, offer_id: str, user_id: str, per_user_limit: int, usage_limit: int | None
    ) -> bool:
        """Atomically record coupon usage respecting global and per-user limits."""
        query: dict[str, Any] = {
            "id": offer_id,
            "is_active": True,
            f"user_usage.{user_id}": {"$lt": per_user_limit},
        }
        if usage_limit is not None:
            query["current_usage"] = {"$lt": usage_limit}

        # Also permit if user hasn't redeemed before
        fallback_query: dict[str, Any] = {
            "id": offer_id,
            "is_active": True,
            f"user_usage.{user_id}": {"$exists": False},
        }
        if usage_limit is not None:
            fallback_query["current_usage"] = {"$lt": usage_limit}

        update = {
            "$inc": {
                "current_usage": 1,
                f"user_usage.{user_id}": 1,
            }
        }

        res = await self.offers.update_one(query, update)
        if res.modified_count > 0:
            return True

        res2 = await self.offers.update_one(fallback_query, update)
        return res2.modified_count > 0
