"""MongoDB repository for Offers, Coupon management, and Redemptions."""

from datetime import UTC, datetime
from typing import Any

from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo import ASCENDING, IndexModel

from app.modules.offer.offer_model import OfferInDB


class OfferRepository:
    """Repository accessing `offers` and `offer_redemptions` collections."""

    def __init__(self, db: AsyncIOMotorDatabase[dict[str, Any]]) -> None:
        self.db = db
        self.offers: AsyncIOMotorCollection[dict[str, Any]] = db["offers"]
        self.redemptions: AsyncIOMotorCollection[dict[str, Any]] = db["offer_redemptions"]

    async def ensure_indexes(self) -> None:
        """Create indexes for fast lookup and unique coupon codes."""
        await self.offers.create_indexes([
            IndexModel([("code", ASCENDING)], unique=True, name="idx_offer_code_unique"),
            IndexModel(
                [("is_active", ASCENDING), ("valid_from", ASCENDING), ("valid_until", ASCENDING)],
                name="idx_offer_validity",
            ),
        ])

        await self.redemptions.create_indexes([
            IndexModel(
                [("offer_id", ASCENDING), ("payment_id", ASCENDING)],
                unique=True,
                name="idx_offer_redemptions_offer_payment_unique",
            ),
            IndexModel([("user_id", ASCENDING)], name="idx_offer_redemptions_user"),
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
        self,
        offer_id: str,
        user_id: str,
        per_user_limit: int,
        usage_limit: int | None,
        payment_id: str | None = None,
    ) -> bool:
        """Atomically record coupon usage respecting global and per-user limits, idempotent per payment_id."""
        now = datetime.now(UTC)
        if payment_id:
            # Check if this payment already redeemed this offer
            existing = await self.redemptions.find_one({"offer_id": offer_id, "payment_id": payment_id})
            if existing:
                return True
            try:
                await self.redemptions.insert_one({
                    "offer_id": offer_id,
                    "payment_id": payment_id,
                    "user_id": user_id,
                    "redeemed_at": now,
                })
            except Exception:
                # Concurrent duplicate redemption for same payment
                return True

        query: dict[str, Any] = {
            "id": offer_id,
            "is_active": True,
            f"user_usage.{user_id}": {"$lt": per_user_limit},
        }
        if usage_limit is not None:
            query["current_usage"] = {"$lt": usage_limit}

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
