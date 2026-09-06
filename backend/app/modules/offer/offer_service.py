"""Domain business logic for Offer validation and Authoritative Price Calculation."""

import uuid
from datetime import UTC, datetime

from app.common.exceptions.app_exceptions import BadRequestException, NotFoundException
from app.common.exceptions.error_codes import ErrorCode
from app.common.utils.datetime_utils import utc_now
from app.modules.offer.offer_constants import DiscountType, OfferStatus
from app.modules.offer.offer_model import OfferInDB
from app.modules.offer.offer_repository import OfferRepository
from app.modules.offer.offer_schema import (
    CreateOfferRequest,
    OfferResponse,
    PricingBreakdownResponse,
)


class OfferService:
    """Service handling offer lifecycle and price computation."""

    def __init__(self, offer_repo: OfferRepository) -> None:
        self.offer_repo = offer_repo

    async def create_offer(self, req: CreateOfferRequest) -> OfferResponse:
        """Create new promotional coupon."""
        existing = await self.offer_repo.get_by_code(req.code)
        if existing:
            raise BadRequestException(
                message=f"Offer code '{req.code.upper()}' already exists",
                code=ErrorCode.RESOURCE_ALREADY_EXISTS,
            )

        now = utc_now()
        offer = OfferInDB(
            id=str(uuid.uuid4()),
            code=req.code.upper().strip(),
            title=req.title,
            description=req.description,
            discount_type=req.discount_type,
            discount_value=req.discount_value,
            min_order_minor=req.min_order_minor,
            max_discount_minor=req.max_discount_minor,
            usage_limit=req.usage_limit,
            per_user_limit=req.per_user_limit,
            valid_from=req.valid_from,
            valid_until=req.valid_until,
            is_active=req.is_active,
            created_at=now,
            updated_at=now,
        )
        saved = await self.offer_repo.create_offer(offer)
        return OfferResponse.from_db(saved)

    async def list_active_offers(self) -> list[OfferResponse]:
        """Fetch all eligible active offers."""
        offers = await self.offer_repo.list_active_offers()
        return [OfferResponse.from_db(o) for o in offers if o.status == OfferStatus.ACTIVE]

    async def validate_and_calculate_discount(
        self, code: str, user_id: str, base_amount_minor: int
    ) -> tuple[OfferInDB, int]:
        """Validate coupon eligibility and return (OfferInDB, discount_minor)."""
        offer = await self.offer_repo.get_by_code(code)
        if not offer:
            raise NotFoundException(
                message=f"Coupon code '{code}' not found",
                code=ErrorCode.OFFER_NOT_FOUND,
            )

        now = datetime.now(UTC)
        if not offer.is_active or now < offer.valid_from:
            raise BadRequestException(
                message="This offer is not active yet",
                code=ErrorCode.OFFER_NOT_ACTIVE,
            )

        if now > offer.valid_until:
            raise BadRequestException(
                message="This coupon code has expired",
                code=ErrorCode.OFFER_EXPIRED,
            )

        if offer.usage_limit is not None and offer.current_usage >= offer.usage_limit:
            raise BadRequestException(
                message="This coupon code has reached its maximum global usage limit",
                code=ErrorCode.OFFER_USAGE_EXCEEDED,
            )

        user_count = offer.user_usage.get(user_id, 0)
        if user_count >= offer.per_user_limit:
            raise BadRequestException(
                message="You have already reached the maximum usage limit for this coupon",
                code=ErrorCode.OFFER_USER_LIMIT_REACHED,
            )

        if base_amount_minor < offer.min_order_minor:
            min_rs = offer.min_order_minor // 100
            raise BadRequestException(
                message=f"Minimum purchase of ₹{min_rs} required to use this coupon",
                code=ErrorCode.OFFER_MINIMUM_ORDER_NOT_MET,
            )

        # Compute discount in minor units
        if offer.discount_type == DiscountType.PERCENTAGE:
            # integer division rounded down: (base * percentage) // 100
            discount = (base_amount_minor * offer.discount_value) // 100
            if offer.max_discount_minor is not None:
                discount = min(discount, offer.max_discount_minor)
        else:
            discount = offer.discount_value

        # Financial integrity check: discount cannot exceed base amount
        discount = max(0, min(discount, base_amount_minor))
        return offer, discount

    async def calculate_pricing(
        self, base_amount_minor: int, user_id: str, offer_code: str | None = None
    ) -> PricingBreakdownResponse:
        """Authoritative pricing calculation engine for checkout."""
        if not offer_code:
            return PricingBreakdownResponse(
                base_amount_minor=base_amount_minor,
                discount_amount_minor=0,
                payable_amount_minor=base_amount_minor,
            )

        offer, discount = await self.validate_and_calculate_discount(
            code=offer_code, user_id=user_id, base_amount_minor=base_amount_minor
        )
        payable = base_amount_minor - discount

        return PricingBreakdownResponse(
            base_amount_minor=base_amount_minor,
            discount_amount_minor=discount,
            payable_amount_minor=payable,
            offer_applied=OfferResponse.from_db(offer),
            message=f"Coupon '{offer.code}' applied successfully!",
        )

    async def record_usage_atomic(
        self, offer_id: str, user_id: str, payment_id: str | None = None
    ) -> bool:
        """Atomically increment coupon usage upon confirmed payment."""
        offer = await self.offer_repo.get_by_id(offer_id)
        if not offer:
            return False
        return await self.offer_repo.increment_usage_atomic(
            offer_id=offer.id,
            user_id=user_id,
            per_user_limit=offer.per_user_limit,
            usage_limit=offer.usage_limit,
            payment_id=payment_id,
        )
