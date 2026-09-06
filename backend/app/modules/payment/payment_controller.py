"""Presentation controller for Payment endpoints."""

from fastapi import Request

from app.common.responses.api_response import ApiResponse, success_response
from app.modules.payment.payment_schema import (
    CreatePaymentRequest,
    PaymentConfigResponse,
    PaymentResponse,
    VerifyPaymentRequest,
)
from app.modules.payment.payment_service import PaymentService
from app.modules.user.user_model import UserInDB


class PaymentController:
    """Controller handling HTTP serialization for payment operations."""

    def __init__(self, service: PaymentService) -> None:
        self.service = service

    def get_public_config(self) -> ApiResponse[PaymentConfigResponse]:
        config = self.service.get_public_config()
        return success_response(data=config)

    async def initiate_payment(
        self, caller: UserInDB, req: CreatePaymentRequest
    ) -> ApiResponse[PaymentResponse]:
        res = await self.service.initiate_payment(caller=caller, req=req)
        return success_response(data=res, message="Payment initiated")

    async def verify_payment(
        self, caller: UserInDB, payment_id: str, req: VerifyPaymentRequest
    ) -> ApiResponse[PaymentResponse]:
        res = await self.service.verify_payment(caller=caller, payment_id=payment_id, req=req)
        return success_response(data=res, message="Payment verified and processed successfully")

    async def get_payment(
        self, caller: UserInDB, payment_id: str
    ) -> ApiResponse[PaymentResponse]:
        res = await self.service.get_payment(caller=caller, payment_id=payment_id)
        return success_response(data=res)

    async def process_webhook(self, request: Request) -> ApiResponse[dict[str, bool]]:
        body = await request.body()
        sig = (
            request.headers.get("X-Razorpay-Signature")
            or request.headers.get("X-Payment-Signature")
            or ""
        )
        handled = await self.service.process_webhook(payload_bytes=body, signature_header=sig)
        return success_response(data={"processed": handled})
