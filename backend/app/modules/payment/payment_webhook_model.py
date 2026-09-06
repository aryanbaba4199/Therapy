"""MongoDB model for tracking and deduplicating payment provider webhook events."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.common.utils.datetime_utils import ensure_utc, utc_now
from app.modules.payment.payment_constants import PaymentProviderName, WebhookEventStatus


class PaymentWebhookEventInDB(BaseModel):
    """Event log record stored in `payment_webhook_events` collection."""

    id: str = Field(description="Internal webhook event UUID")
    provider: PaymentProviderName = Field(description="Payment provider (e.g. razorpay, mock)")
    event_id: str = Field(description="Unique provider-assigned event ID")
    event_type: str = Field(description="Event name (e.g. payment.captured, order.paid)")
    payload_hash: str = Field(description="SHA256 hash of raw webhook payload")
    status: WebhookEventStatus = Field(default=WebhookEventStatus.PENDING)
    error_message: str | None = Field(default=None)
    received_at: datetime = Field(default_factory=utc_now)
    processed_at: datetime | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("received_at", "processed_at", mode="after")
    @classmethod
    def ensure_tz(cls, v: datetime | None) -> datetime | None:
        return ensure_utc(v) if v is not None else None

    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        d = super().model_dump(*args, **kwargs)
        for key in ["received_at", "processed_at"]:
            if key in d and isinstance(d[key], datetime):
                d[key] = ensure_utc(d[key])
        return d
