"""API endpoints for Payments, Configuration, and Webhook processing."""

from fastapi import APIRouter, Depends, Request

from app.common.responses.api_response import ApiResponse
from app.modules.auth.auth_dependency import get_current_active_user
from app.modules.payment.payment_controller import PaymentController
from app.modules.payment.payment_dependency import get_payment_service
from app.modules.payment.payment_schema import (
    CreatePaymentRequest,
    PaymentConfigResponse,
    PaymentResponse,
    VerifyPaymentRequest,
)
from app.modules.payment.payment_service import PaymentService
from app.modules.user.user_model import UserInDB

router = APIRouter(prefix="/payments", tags=["Payments & Commercial"])


def get_payment_controller(
    service: PaymentService = Depends(get_payment_service),
) -> PaymentController:
    return PaymentController(service=service)


@router.get(
    "/config",
    response_model=ApiResponse[PaymentConfigResponse],
    summary="Get public payment provider configuration",
)
def get_payment_config(
    controller: PaymentController = Depends(get_payment_controller),
) -> ApiResponse[PaymentConfigResponse]:
    return controller.get_public_config()


@router.post(
    "",
    response_model=ApiResponse[PaymentResponse],
    status_code=201,
    summary="Initiate payment for booking reservation or package",
)
async def initiate_payment(
    req: CreatePaymentRequest,
    current_user: UserInDB = Depends(get_current_active_user),
    controller: PaymentController = Depends(get_payment_controller),
) -> ApiResponse[PaymentResponse]:
    return await controller.initiate_payment(caller=current_user, req=req)


@router.get(
    "/{payment_id}",
    response_model=ApiResponse[PaymentResponse],
    summary="Get payment details and verification status",
)
async def get_payment(
    payment_id: str,
    current_user: UserInDB = Depends(get_current_active_user),
    controller: PaymentController = Depends(get_payment_controller),
) -> ApiResponse[PaymentResponse]:
    return await controller.get_payment(caller=current_user, payment_id=payment_id)


@router.post(
    "/{payment_id}/verify",
    response_model=ApiResponse[PaymentResponse],
    summary="Verify gateway payment signature and confirm transaction",
)
async def verify_payment(
    payment_id: str,
    req: VerifyPaymentRequest,
    current_user: UserInDB = Depends(get_current_active_user),
    controller: PaymentController = Depends(get_payment_controller),
) -> ApiResponse[PaymentResponse]:
    return await controller.verify_payment(
        caller=current_user, payment_id=payment_id, req=req
    )


@router.post(
    "/webhook",
    response_model=ApiResponse[dict[str, bool]],
    summary="Gateway webhook listener for async payment reconciliation",
)
async def handle_webhook(
    request: Request,
    controller: PaymentController = Depends(get_payment_controller),
) -> ApiResponse[dict[str, bool]]:
    return await controller.process_webhook(request)


@router.post(
    "/webhooks/razorpay",
    response_model=ApiResponse[dict[str, bool]],
    summary="Razorpay specific webhook listener with raw payload validation",
)
async def handle_razorpay_webhook(
    request: Request,
    controller: PaymentController = Depends(get_payment_controller),
) -> ApiResponse[dict[str, bool]]:
    return await controller.process_webhook(request)
