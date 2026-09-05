"""Pydantic schemas for Package products and User entitlements."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.package.package_constants import PackageStatus
from app.modules.package.package_model import PackageProductInDB, UserPackageInDB


class PackageProductResponse(BaseModel):
    """Public representation of a sellable therapy package."""

    id: str
    title: str
    description: str
    session_count: int
    validity_days: int
    price_minor: int
    currency: str
    is_active: bool

    @classmethod
    def from_db(cls, doc: PackageProductInDB) -> "PackageProductResponse":
        return cls(
            id=doc.id,
            title=doc.title,
            description=doc.description,
            session_count=doc.session_count,
            validity_days=doc.validity_days,
            price_minor=doc.price_minor,
            currency=doc.currency,
            is_active=doc.is_active,
        )


class CreatePackageProductRequest(BaseModel):
    """Admin payload to create a new therapy package product."""

    title: str
    description: str
    session_count: int = Field(ge=1)
    validity_days: int = Field(ge=1)
    price_minor: int = Field(ge=0)
    currency: str = "INR"
    is_active: bool = True


class UserPackageResponse(BaseModel):
    """User-owned session balance."""

    id: str
    user_id: str
    package_product_id: str
    title: str
    total_sessions: int
    remaining_sessions: int
    purchased_at: datetime
    expires_at: datetime
    status: PackageStatus
    is_usable: bool

    @classmethod
    def from_db(cls, doc: UserPackageInDB) -> "UserPackageResponse":
        return cls(
            id=doc.id,
            user_id=doc.user_id,
            package_product_id=doc.package_product_id,
            title=doc.title,
            total_sessions=doc.total_sessions,
            remaining_sessions=doc.remaining_sessions,
            purchased_at=doc.purchased_at,
            expires_at=doc.expires_at,
            status=doc.status,
            is_usable=doc.is_usable,
        )


class PurchasePackageRequest(BaseModel):
    """Payload to initiate purchase of a package product."""

    package_product_id: str
    idempotency_key: str | None = None
