"""MongoDB models for Package products and User package entitlements."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.common.utils.datetime_utils import ensure_utc, utc_now
from app.modules.package.package_constants import PackageStatus


class PackageProductInDB(BaseModel):
    """Sellable package template stored in `package_products` collection."""

    id: str = Field(description="Unique package template UUID")
    title: str = Field(description="Package title e.g. 'Mindful Journey (5 Sessions)'")
    description: str = Field(description="Package details and terms")
    session_count: int = Field(ge=1, description="Total sessions included in bundle")
    validity_days: int = Field(ge=1, description="Validity period in days from purchase")
    price_minor: int = Field(ge=0, description="Package price in minor units (e.g. 450000 for ₹4500)")
    currency: str = Field(default="INR", description="Currency code")
    is_active: bool = Field(default=True, description="Whether available for purchase")
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("created_at", "updated_at", mode="after")
    @classmethod
    def ensure_tz(cls, v: datetime | None) -> datetime | None:
        return ensure_utc(v) if v is not None else None

    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        d = super().model_dump(*args, **kwargs)
        for key in ["created_at", "updated_at"]:
            if key in d and isinstance(d[key], datetime):
                d[key] = ensure_utc(d[key])
        return d


class UserPackageInDB(BaseModel):
    """User-owned package entitlement stored in `user_packages` collection."""

    id: str = Field(description="Unique user package UUID")
    user_id: str = Field(description="Client user UUID")
    package_product_id: str = Field(description="Referenced package product UUID")
    title: str = Field(description="Snapshot of package product title")
    total_sessions: int = Field(ge=1, description="Initial total sessions")
    remaining_sessions: int = Field(ge=0, description="Available sessions balance")
    purchased_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime = Field(description="Entitlement expiration timestamp in UTC")
    payment_id: str | None = Field(default=None, description="Fulfilling payment ID")
    consumed_payment_ids: list[str] = Field(
        default_factory=list, description="Payment IDs for which session credits were deducted"
    )
    status: PackageStatus = Field(default=PackageStatus.ACTIVE)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("purchased_at", "expires_at", "created_at", "updated_at", mode="after")
    @classmethod
    def ensure_tz(cls, v: datetime | None) -> datetime | None:
        return ensure_utc(v) if v is not None else None

    @property
    def is_usable(self) -> bool:
        now = datetime.now(UTC)
        return (
            self.status == PackageStatus.ACTIVE
            and self.remaining_sessions > 0
            and now <= self.expires_at
        )

    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        d = super().model_dump(*args, **kwargs)
        for key in ["purchased_at", "expires_at", "created_at", "updated_at"]:
            if key in d and isinstance(d[key], datetime):
                d[key] = ensure_utc(d[key])
        return d
