"""Payment entity factory for deterministic test data."""

import uuid
from typing import Any

from app.common.utils.datetime_utils import utc_now
from app.modules.payment.payment_constants import (
    FulfillmentStatus,
    PaymentProviderName,
    PaymentStatus,
    PaymentTargetType,
)
from app.modules.payment.payment_model import PaymentInDB, PaymentPricingSnapshot


class PaymentFactory:
    @staticmethod
    def build(
        *,
        id: str | None = None,
        user_id: str | None = None,
        target_type: PaymentTargetType = PaymentTargetType.BOOKING,
        target_id: str | None = None,
        amount_minor: int = 150000,
        currency: str = "INR",
        status: PaymentStatus = PaymentStatus.PENDING,
        provider: PaymentProviderName = PaymentProviderName.MOCK,
        provider_order_id: str | None = None,
        provider_payment_id: str | None = None,
        fulfillment_status: FulfillmentStatus = FulfillmentStatus.PENDING,
    ) -> PaymentInDB:
        p_id = id or str(uuid.uuid4())
        u_id = user_id or str(uuid.uuid4())
        t_id = target_id or str(uuid.uuid4())
        now = utc_now()

        return PaymentInDB(
            id=p_id,
            user_id=u_id,
            target_type=target_type,
            target_id=t_id,
            amount_minor=amount_minor,
            currency=currency,
            status=status,
            provider=provider,
            provider_order_id=provider_order_id or f"order_{p_id[:12]}",
            provider_payment_id=provider_payment_id,
            fulfillment_status=fulfillment_status,
            pricing=PaymentPricingSnapshot(
                base_amount_minor=amount_minor,
                discount_amount_minor=0,
                payable_amount_minor=amount_minor,
                currency=currency,
            ),
            created_at=now,
            updated_at=now,
        )

    @staticmethod
    async def create(mock_db: Any, **kwargs: Any) -> PaymentInDB:
        payment = PaymentFactory.build(**kwargs)
        await mock_db["payments"].insert_one(payment.model_dump(mode="json"))
        return payment
