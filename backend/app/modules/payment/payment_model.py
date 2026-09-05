"""MongoDB models for the Payment and Commercial layer."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.common.utils.datetime_utils import ensure_utc, utc_now
from app.modules.payment.payment_constants import (
    PaymentMethod,
    PaymentProviderName,
    PaymentStatus,
    PaymentTargetType,
)


class PaymentPricingSnapshot(BaseModel):
    """Immutable monetary breakdown stored with the payment record."""

    base_amount_minor: int = Field(ge=0, description="Base consultation or package price")
    discount_amount_minor: int = Field(ge=0, default=0, description="Deduction from offer or package")
    payable_amount_minor: int = Field(ge=0, description="Net amount charged through payment gateway")
    currency: str = Field(default="INR", description="Currency ISO code")
    offer_code: str | None = Field(default=None, description="Applied promotional coupon code")
    user_package_id: str | None = Field(default=None, description="Applied user package if redeemed")


class PaymentInDB(BaseModel):
    """Payment record stored in `payments` collection."""

    id: str = Field(description="Unique internal payment UUID")
    user_id: str = Field(description="Client user UUID")
    target_type: PaymentTargetType = Field(description="booking or package")
    target_id: str = Field(description="Reservation/Booking UUID or PackageProduct UUID")
    amount_minor: int = Field(ge=0, description="Payable amount in minor units")
    currency: str = Field(default="INR")
    status: PaymentStatus = Field(default=PaymentStatus.CREATED)
    provider: PaymentProviderName = Field(default=PaymentProviderName.MOCK)
    provider_order_id: str | None = Field(default=None, description="Gateway order ID")
    provider_payment_id: str | None = Field(default=None, description="Gateway payment ID")
    provider_signature: str | None = Field(default=None, description="Verification signature")
    payment_method: PaymentMethod | None = Field(default=None)
    pricing: PaymentPricingSnapshot
    idempotency_key: str | None = Field(default=None, description="Unique client idempotency token")
    failure_code: str | None = Field(default=None)
    failure_message: str | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)
    paid_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("paid_at", "created_at", "updated_at", mode="after")
    @classmethod
    def ensure_tz(cls, v: datetime | None) -> datetime | None:
        return ensure_utc(v) if v is not None else None

    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        d = super().model_dump(*args, **kwargs)
        for key in ["paid_at", "created_at", "updated_at"]:
            if key in d and isinstance(d[key], datetime):
                d[key] = ensure_utc(d[key])
        return d
