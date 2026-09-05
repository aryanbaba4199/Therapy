"""Pydantic schemas for Offer validation and price calculation."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.offer.offer_constants import DiscountType, OfferStatus
from app.modules.offer.offer_model import OfferInDB


class OfferResponse(BaseModel):
    """Public promotional offer representation."""

    id: str
    code: str
    title: str
    description: str
    discount_type: DiscountType
    discount_value: int
    min_order_minor: int
    max_discount_minor: int | None
    valid_from: datetime
    valid_until: datetime
    status: OfferStatus

    @classmethod
    def from_db(cls, doc: OfferInDB) -> "OfferResponse":
        return cls(
            id=doc.id,
            code=doc.code,
            title=doc.title,
            description=doc.description,
            discount_type=doc.discount_type,
            discount_value=doc.discount_value,
            min_order_minor=doc.min_order_minor,
            max_discount_minor=doc.max_discount_minor,
            valid_from=doc.valid_from,
            valid_until=doc.valid_until,
            status=doc.status,
        )


class CreateOfferRequest(BaseModel):
    """Payload to configure a new promotional offer (Admin/Staff)."""

    code: str = Field(min_length=3, max_length=20)
    title: str
    description: str = ""
    discount_type: DiscountType
    discount_value: int = Field(gt=0)
    min_order_minor: int = Field(default=0, ge=0)
    max_discount_minor: int | None = Field(default=None, gt=0)
    usage_limit: int | None = Field(default=None, gt=0)
    per_user_limit: int = Field(default=1, gt=0)
    valid_from: datetime
    valid_until: datetime
    is_active: bool = True


class ValidateOfferRequest(BaseModel):
    """Payload to validate a coupon code against a purchase amount."""

    code: str
    base_amount_minor: int = Field(ge=0)


class PricingCalculationRequest(BaseModel):
    """Request payload to authoritatively calculate payable amount."""

    base_amount_minor: int = Field(ge=0)
    offer_code: str | None = None
    user_package_id: str | None = None


class PricingBreakdownResponse(BaseModel):
    """Authoritative pricing calculation breakdown."""

    base_amount_minor: int
    discount_amount_minor: int
    payable_amount_minor: int
    currency: str = "INR"
    offer_applied: OfferResponse | None = None
    package_applied: bool = False
    message: str | None = None
