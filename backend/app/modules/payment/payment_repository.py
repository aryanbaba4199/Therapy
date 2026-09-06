"""MongoDB repository for Payments and Commercial transactions."""

from datetime import UTC, datetime
from typing import Any

from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo import ASCENDING, IndexModel

from app.modules.payment.payment_constants import (
    FulfillmentStatus,
    PaymentMethod,
    PaymentStatus,
)
from app.modules.payment.payment_model import PaymentInDB


class PaymentRepository:
    """Repository accessing `payments` collection."""

    def __init__(self, db: AsyncIOMotorDatabase[dict[str, Any]]) -> None:
        self.db = db
        self.payments: AsyncIOMotorCollection[dict[str, Any]] = db["payments"]

    async def ensure_indexes(self) -> None:
        """Initialize database indexes."""
        await self.payments.create_indexes([
            IndexModel([("id", ASCENDING)], unique=True, name="idx_payment_id"),
            IndexModel(
                [("user_id", ASCENDING), ("created_at", ASCENDING)],
                name="idx_payment_user_created",
            ),
            IndexModel(
                [("provider_order_id", ASCENDING)],
                unique=True,
                sparse=True,
                name="idx_payment_provider_order",
            ),
            IndexModel(
                [("idempotency_key", ASCENDING)],
                unique=True,
                sparse=True,
                name="idx_payment_idempotency",
            ),
            IndexModel([("target_id", ASCENDING)], name="idx_payment_target_id"),
        ])

    async def create_payment(self, payment: PaymentInDB) -> PaymentInDB:
        await self.payments.insert_one(payment.model_dump())
        return payment

    async def get_by_id(self, payment_id: str) -> PaymentInDB | None:
        doc = await self.payments.find_one({"id": payment_id})
        return PaymentInDB(**doc) if doc else None

    async def get_by_provider_order_id(self, provider_order_id: str) -> PaymentInDB | None:
        doc = await self.payments.find_one({"provider_order_id": provider_order_id})
        return PaymentInDB(**doc) if doc else None

    async def get_by_idempotency_key(self, idempotency_key: str) -> PaymentInDB | None:
        doc = await self.payments.find_one({"idempotency_key": idempotency_key})
        return PaymentInDB(**doc) if doc else None

    async def list_user_payments(self, user_id: str, limit: int = 50) -> list[PaymentInDB]:
        cursor = self.payments.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [PaymentInDB(**d) for d in docs]

    async def mark_payment_paid(
        self,
        payment_id: str,
        provider_payment_id: str,
        provider_signature: str | None = None,
        payment_method: PaymentMethod | None = None,
    ) -> PaymentInDB | None:
        """Atomically transition payment to PAID state."""
        now = datetime.now(UTC)
        query = {
            "id": payment_id,
            "status": {"$in": [PaymentStatus.CREATED.value, PaymentStatus.PENDING.value]},
        }
        updates: dict[str, Any] = {
            "status": PaymentStatus.PAID.value,
            "provider_payment_id": provider_payment_id,
            "paid_at": now,
            "updated_at": now,
        }
        if provider_signature:
            updates["provider_signature"] = provider_signature
        if payment_method:
            updates["payment_method"] = payment_method.value

        res = await self.payments.find_one_and_update(
            query, {"$set": updates}, return_document=True
        )
        return PaymentInDB(**res) if res else None

    async def mark_payment_failed(
        self, payment_id: str, failure_code: str, failure_message: str
    ) -> PaymentInDB | None:
        now = datetime.now(UTC)
        res = await self.payments.find_one_and_update(
            {"id": payment_id, "status": {"$ne": PaymentStatus.PAID.value}},
            {
                "$set": {
                    "status": PaymentStatus.FAILED.value,
                    "failure_code": failure_code,
                    "failure_message": failure_message,
                    "updated_at": now,
                }
            },
            return_document=True,
        )
        return PaymentInDB(**res) if res else None

    async def update_fulfillment_status(
        self, payment_id: str, status: FulfillmentStatus
    ) -> PaymentInDB | None:
        """Update commercial fulfillment lifecycle state."""
        now = datetime.now(UTC)
        res = await self.payments.find_one_and_update(
            {"id": payment_id},
            {"$set": {"fulfillment_status": status.value, "updated_at": now}},
            return_document=True,
        )
        return PaymentInDB(**res) if res else None
