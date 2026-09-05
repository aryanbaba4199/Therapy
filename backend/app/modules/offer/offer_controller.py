"""Presentation controller for Offer endpoints."""

from app.common.responses.api_response import ApiResponse, success_response
from app.modules.offer.offer_schema import (
    CreateOfferRequest,
    OfferResponse,
    PricingBreakdownResponse,
    ValidateOfferRequest,
)
from app.modules.offer.offer_service import OfferService
from app.modules.user.user_model import UserInDB


class OfferController:
    """Controller handling HTTP serialization for offers."""

    def __init__(self, service: OfferService) -> None:
        self.service = service

    async def create_offer(self, req: CreateOfferRequest) -> ApiResponse[OfferResponse]:
        res = await self.service.create_offer(req)
        return success_response(data=res, message="Offer created successfully")

    async def list_active_offers(self) -> ApiResponse[list[OfferResponse]]:
        res = await self.service.list_active_offers()
        return success_response(data=res)

    async def validate_offer(
        self, caller: UserInDB, req: ValidateOfferRequest
    ) -> ApiResponse[PricingBreakdownResponse]:
        res = await self.service.calculate_pricing(
            base_amount_minor=req.base_amount_minor,
            user_id=caller.id,
            offer_code=req.code,
        )
        return success_response(data=res)

