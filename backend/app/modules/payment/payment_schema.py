"""Pydantic schemas for Payment requests and responses."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.payment.payment_constants import (
    FulfillmentStatus,
    PaymentMethod,
    PaymentProviderName,
    PaymentStatus,
    PaymentTargetType,
)
from app.modules.payment.payment_model import PaymentInDB, PaymentPricingSnapshot


class CreatePaymentRequest(BaseModel):
    """Payload to initiate a payment transaction."""

    target_type: PaymentTargetType = Field(description="booking or package")
    target_id: str = Field(description="Reservation ID or PackageProduct ID")
    offer_code: str | None = None
    user_package_id: str | None = Field(
        default=None, description="If paying for booking using existing package credit"
    )
    idempotency_key: str | None = Field(
        default=None, description="Client idempotency key to prevent double charging"
    )


class VerifyPaymentRequest(BaseModel):
    """Payload sent by client after completing gateway checkout."""

    provider_order_id: str
    provider_payment_id: str
    provider_signature: str
    payment_method: PaymentMethod = PaymentMethod.MOCK


class PaymentResponse(BaseModel):
    """Public representation of payment order state."""

    id: str
    user_id: str
    target_type: PaymentTargetType
    target_id: str
    amount_minor: int
    currency: str
    status: PaymentStatus
    fulfillment_status: FulfillmentStatus = FulfillmentStatus.PENDING
    provider: PaymentProviderName
    provider_order_id: str | None
    provider_payment_id: str | None
    payment_method: PaymentMethod | None
    pricing: PaymentPricingSnapshot
    paid_at: datetime | None
    created_at: datetime

    @classmethod
    def from_db(cls, doc: PaymentInDB) -> "PaymentResponse":
        return cls(
            id=doc.id,
            user_id=doc.user_id,
            target_type=doc.target_type,
            target_id=doc.target_id,
            amount_minor=doc.amount_minor,
            currency=doc.currency,
            status=doc.status,
            fulfillment_status=doc.fulfillment_status,
            provider=doc.provider,
            provider_order_id=doc.provider_order_id,
            provider_payment_id=doc.provider_payment_id,
            payment_method=doc.payment_method,
            pricing=doc.pricing,
            paid_at=doc.paid_at,
            created_at=doc.created_at,
        )


class WebhookPayload(BaseModel):
    """Standardized incoming webhook event payload."""

    event: str
    provider_order_id: str
    provider_payment_id: str
    amount_minor: int
    currency: str = "INR"
    status: str
