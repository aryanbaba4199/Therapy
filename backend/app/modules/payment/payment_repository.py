"""MongoDB repository for Payments, Commercial transactions, and Webhook Events."""

from datetime import UTC, datetime, timedelta
from typing import Any

from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo import ASCENDING, IndexModel

from app.modules.payment.payment_constants import (
    FulfillmentStatus,
    PaymentMethod,
    PaymentProviderName,
    PaymentStatus,
    WebhookEventStatus,
)
from app.modules.payment.payment_model import PaymentInDB
from app.modules.payment.payment_webhook_model import PaymentWebhookEventInDB


class PaymentRepository:
    """Repository accessing `payments` and `payment_webhook_events` collections."""

    def __init__(self, db: AsyncIOMotorDatabase[dict[str, Any]]) -> None:
        self.db = db
        self.payments: AsyncIOMotorCollection[dict[str, Any]] = db["payments"]
        self.webhook_events: AsyncIOMotorCollection[dict[str, Any]] = db["payment_webhook_events"]

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
            IndexModel(
                [("fulfillment_status", ASCENDING), ("processing_started_at", ASCENDING)],
                name="idx_payment_fulfillment_recovery",
            ),
        ])

        await self.webhook_events.create_indexes([
            IndexModel([("id", ASCENDING)], unique=True, name="idx_webhook_events_id"),
            IndexModel(
                [("provider", ASCENDING), ("event_id", ASCENDING)],
                unique=True,
                name="idx_webhook_events_provider_event_unique",
            ),
            IndexModel([("received_at", ASCENDING)], name="idx_webhook_events_received"),
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

    async def claim_fulfillment_ownership(
        self,
        payment_id: str,
        worker_id: str,
        stale_timeout_seconds: int = 60,
    ) -> PaymentInDB | None:
        """Atomically claim commercial fulfillment execution rights.

        Succeeds if:
        1. status is PAID and fulfillment_status is PENDING or FAILED.
        2. status is PAID and fulfillment_status is PROCESSING but stale (processing_started_at < now - 60s).
        """
        now = datetime.now(UTC)
        stale_cutoff = now - timedelta(seconds=stale_timeout_seconds)

        query: dict[str, Any] = {
            "id": payment_id,
            "status": PaymentStatus.PAID.value,
            "$or": [
                {"fulfillment_status": {"$in": [FulfillmentStatus.PENDING.value, FulfillmentStatus.FAILED.value]}},
                {
                    "fulfillment_status": FulfillmentStatus.PROCESSING.value,
                    "processing_started_at": {"$lt": stale_cutoff},
                },
            ],
        }

        update = {
            "$set": {
                "fulfillment_status": FulfillmentStatus.PROCESSING.value,
                "processing_started_at": now,
                "processing_worker": worker_id,
                "updated_at": now,
            },
            "$inc": {"processing_attempt": 1},
        }

        res = await self.payments.find_one_and_update(
            query, update, return_document=True
        )
        return PaymentInDB(**res) if res else None

    async def mark_fulfillment_success(self, payment_id: str) -> PaymentInDB | None:
        """Mark commercial fulfillment as FULFILLED."""
        now = datetime.now(UTC)
        res = await self.payments.find_one_and_update(
            {"id": payment_id},
            {
                "$set": {
                    "fulfillment_status": FulfillmentStatus.FULFILLED.value,
                    "last_fulfillment_error": None,
                    "updated_at": now,
                }
            },
            return_document=True,
        )
        return PaymentInDB(**res) if res else None

    async def mark_fulfillment_failed(
        self, payment_id: str, error_message: str
    ) -> PaymentInDB | None:
        """Mark commercial fulfillment as FAILED with error message."""
        now = datetime.now(UTC)
        res = await self.payments.find_one_and_update(
            {"id": payment_id},
            {
                "$set": {
                    "fulfillment_status": FulfillmentStatus.FAILED.value,
                    "last_fulfillment_error": error_message,
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

    # --- Webhook Events Logging & Deduplication ---

    async def record_webhook_event(self, event: PaymentWebhookEventInDB) -> bool:
        """Atomically record incoming webhook event.

        Returns True if newly inserted, False if duplicate event (already recorded).
        """
        try:
            await self.webhook_events.insert_one(event.model_dump())
            return True
        except Exception:
            # DuplicateKeyError or unique index violation
            return False

    async def get_webhook_event(
        self, provider: PaymentProviderName, event_id: str
    ) -> PaymentWebhookEventInDB | None:
        doc = await self.webhook_events.find_one({
            "provider": provider.value if hasattr(provider, "value") else str(provider),
            "event_id": event_id,
        })
        return PaymentWebhookEventInDB(**doc) if doc else None

    async def update_webhook_event_status(
        self,
        event_id: str,
        provider: PaymentProviderName,
        status: WebhookEventStatus,
        error_message: str | None = None,
    ) -> None:
        now = datetime.now(UTC)
        updates: dict[str, Any] = {
            "status": status.value,
            "processed_at": now,
        }
        if error_message:
            updates["error_message"] = error_message
        await self.webhook_events.update_one(
            {
                "provider": provider.value if hasattr(provider, "value") else str(provider),
                "event_id": event_id,
            },
            {"$set": updates},
        )
