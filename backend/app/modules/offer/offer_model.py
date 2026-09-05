"""MongoDB models for Offers and Promotional Coupons."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.common.utils.datetime_utils import ensure_utc, utc_now
from app.modules.offer.offer_constants import DiscountType, OfferStatus


class OfferInDB(BaseModel):
    """Promotional offer document stored in `offers` collection."""

    id: str = Field(description="Unique UUID for the offer")
    code: str = Field(description="Normalized unique coupon code (e.g., OPPAM50)")
    title: str = Field(description="Human-readable promotional title")
    description: str = Field(default="", description="Offer description")
    discount_type: DiscountType = Field(description="Percentage or fixed minor amount")
    discount_value: int = Field(
        description="Discount percentage (e.g. 20 for 20%) or minor amount (e.g. 20000 for ₹200)"
    )
    min_order_minor: int = Field(
        default=0, description="Minimum order amount in minor units (e.g. 50000 for ₹500)"
    )
    max_discount_minor: int | None = Field(
        default=None, description="Cap on maximum discount in minor units for percentage offers"
    )
    usage_limit: int | None = Field(
        default=None, description="Total global redemption limit across all users"
    )
    per_user_limit: int = Field(
        default=1, description="Maximum times an individual user can redeem this code"
    )
    current_usage: int = Field(default=0, description="Global redemption count to date")
    user_usage: dict[str, int] = Field(
        default_factory=dict, description="Map of user_id to redemption count"
    )
    valid_from: datetime = Field(description="Start timestamp in UTC")
    valid_until: datetime = Field(description="Expiry timestamp in UTC")
    is_active: bool = Field(default=True, description="Master operational toggle")
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("valid_from", "valid_until", "created_at", "updated_at", mode="after")
    @classmethod
    def ensure_tz(cls, v: datetime | None) -> datetime | None:
        return ensure_utc(v) if v is not None else None

    @property
    def status(self) -> OfferStatus:
        now = datetime.now(UTC)
        if not self.is_active or now > self.valid_until or now < self.valid_from:
            return OfferStatus.INACTIVE
        if self.usage_limit is not None and self.current_usage >= self.usage_limit:
            return OfferStatus.EXHAUSTED
        return OfferStatus.ACTIVE

    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        d = super().model_dump(*args, **kwargs)
        for key in ["valid_from", "valid_until", "created_at", "updated_at"]:
            if key in d and isinstance(d[key], datetime):
                d[key] = ensure_utc(d[key])
        return d
