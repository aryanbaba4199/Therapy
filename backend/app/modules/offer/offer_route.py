"""API endpoints for Offers and Price Validation."""

from fastapi import APIRouter, Depends

from app.common.responses.api_response import ApiResponse
from app.modules.auth.auth_dependency import get_current_active_user, require_roles
from app.modules.offer.offer_controller import OfferController
from app.modules.offer.offer_dependency import get_offer_service
from app.modules.offer.offer_schema import (
    CreateOfferRequest,
    OfferResponse,
    PricingBreakdownResponse,
    ValidateOfferRequest,
)
from app.modules.offer.offer_service import OfferService
from app.modules.user.user_constants import UserRole
from app.modules.user.user_model import UserInDB

router = APIRouter(prefix="/offers", tags=["Offers & Pricing"])


def get_offer_controller(
    service: OfferService = Depends(get_offer_service),
) -> OfferController:
    return OfferController(service=service)


@router.get(
    "",
    response_model=ApiResponse[list[OfferResponse]],
    summary="List currently active promotional offers",
)
async def list_active_offers(
    controller: OfferController = Depends(get_offer_controller),
) -> ApiResponse[list[OfferResponse]]:
    return await controller.list_active_offers()


@router.post(
    "",
    response_model=ApiResponse[OfferResponse],
    status_code=201,
    summary="Create a new promotional offer (Admin/Staff only)",
)
async def create_offer(
    req: CreateOfferRequest,
    _current_user: UserInDB = Depends(
        require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.STAFF)
    ),
    controller: OfferController = Depends(get_offer_controller),
) -> ApiResponse[OfferResponse]:
    return await controller.create_offer(req)


@router.post(
    "/validate",
    response_model=ApiResponse[PricingBreakdownResponse],
    summary="Validate offer code and calculate net payable amount",
)
async def validate_offer(
    req: ValidateOfferRequest,
    current_user: UserInDB = Depends(get_current_active_user),
    controller: OfferController = Depends(get_offer_controller),
) -> ApiResponse[PricingBreakdownResponse]:
    return await controller.validate_offer(caller=current_user, req=req)
