"""Domain business logic for Payment initiation, verification, and fulfillment."""

import uuid
from datetime import UTC, datetime

from app.common.exceptions.app_exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.common.exceptions.error_codes import ErrorCode
from app.common.utils.datetime_utils import utc_now
from app.core.config import Settings
from app.modules.booking.booking_repository import BookingRepository
from app.modules.booking.booking_schema import ConfirmBookingRequest
from app.modules.booking.booking_service import BookingService
from app.modules.offer.offer_service import OfferService
from app.modules.package.package_service import PackageService
from app.modules.payment.payment_constants import (
    FulfillmentStatus,
    PaymentMethod,
    PaymentProviderName,
    PaymentStatus,
    PaymentTargetType,
)
from app.modules.payment.payment_model import PaymentInDB, PaymentPricingSnapshot
from app.modules.payment.payment_provider import MockPaymentProvider, PaymentProvider
from app.modules.payment.payment_repository import PaymentRepository
from app.modules.payment.payment_schema import (
    CreatePaymentRequest,
    PaymentResponse,
    VerifyPaymentRequest,
)
from app.modules.user.user_model import UserInDB


class PaymentService:
    """Service orchestrating payments, provider interactions, and order fulfillment."""

    def __init__(
        self,
        payment_repo: PaymentRepository,
        booking_repo: BookingRepository,
        booking_service: BookingService,
        offer_service: OfferService,
        package_service: PackageService,
        settings: Settings,
        provider: PaymentProvider | None = None,
    ) -> None:
        self.payment_repo = payment_repo
        self.booking_repo = booking_repo
        self.booking_service = booking_service
        self.offer_service = offer_service
        self.package_service = package_service
        self.settings = settings
        self.provider = provider or MockPaymentProvider()

    async def initiate_payment(
        self, caller: UserInDB, req: CreatePaymentRequest
    ) -> PaymentResponse:
        """Create a payment intent / order for a booking reservation or package purchase."""
        # 1. Check idempotency key if provided
        if req.idempotency_key:
            existing = await self.payment_repo.get_by_idempotency_key(req.idempotency_key)
            if existing:
                if existing.user_id != caller.id:
                    raise ConflictException(
                        message="Idempotency key belongs to another user",
                        code=ErrorCode.PAYMENT_IDEMPOTENCY_CONFLICT,
                    )
                return PaymentResponse.from_db(existing)

        # 2. Resolve target and calculate authoritative base price in minor units
        if req.target_type == PaymentTargetType.BOOKING:
            reservation = await self.booking_repo.get_reservation_by_id(req.target_id)
            if not reservation:
                raise NotFoundException(
                    message="Reservation not found",
                    code=ErrorCode.BOOKING_RESERVATION_NOT_FOUND,
                )
            if reservation.client_id != caller.id:
                raise ForbiddenException(
                    message="Reservation belongs to another user",
                    code=ErrorCode.BOOKING_RESERVATION_FORBIDDEN,
                )
            now = datetime.now(UTC)
            if reservation.expires_at <= now:
                raise BadRequestException(
                    message="Reservation has expired",
                    code=ErrorCode.BOOKING_RESERVATION_EXPIRED,
                )

            # Therapist pricing lookup
            therapist = await self.booking_service.therapist_repo.get_by_id(reservation.therapist_id)
            if not therapist:
                raise NotFoundException(
                    message="Therapist not found",
                    code=ErrorCode.THERAPIST_NOT_FOUND,
                )
            # Authoritative minor units: int(₹amount * 100)
            base_amount_minor = int(round(therapist.pricing.amount * 100))

            # 3. Handle Package session credit redemption (100% discount)
            if req.user_package_id:
                # Validate user owns usable package
                pkgs = await self.package_service.get_usable_packages(caller.id)
                matched_pkg = next((p for p in pkgs if p.id == req.user_package_id), None)
                if not matched_pkg:
                    raise BadRequestException(
                        message="Specified package has no remaining sessions or is expired",
                        code=ErrorCode.PACKAGE_EXHAUSTED,
                    )
                pricing_snapshot = PaymentPricingSnapshot(
                    base_amount_minor=base_amount_minor,
                    discount_amount_minor=base_amount_minor,
                    payable_amount_minor=0,
                    currency="INR",
                    user_package_id=matched_pkg.id,
                )
            else:
                # 4. Authoritative offer / coupon discount calculation
                pricing_res = await self.offer_service.calculate_pricing(
                    base_amount_minor=base_amount_minor,
                    user_id=caller.id,
                    offer_code=req.offer_code,
                )
                pricing_snapshot = PaymentPricingSnapshot(
                    base_amount_minor=pricing_res.base_amount_minor,
                    discount_amount_minor=pricing_res.discount_amount_minor,
                    payable_amount_minor=pricing_res.payable_amount_minor,
                    currency=pricing_res.currency,
                    offer_code=req.offer_code.upper() if req.offer_code else None,
                )

        elif req.target_type == PaymentTargetType.PACKAGE:
            pkg_product = await self.package_service.get_product(req.target_id)
            base_amount_minor = pkg_product.price_minor
            pricing_res = await self.offer_service.calculate_pricing(
                base_amount_minor=base_amount_minor,
                user_id=caller.id,
                offer_code=req.offer_code,
            )
            pricing_snapshot = PaymentPricingSnapshot(
                base_amount_minor=pricing_res.base_amount_minor,
                discount_amount_minor=pricing_res.discount_amount_minor,
                payable_amount_minor=pricing_res.payable_amount_minor,
                currency=pkg_product.currency,
                offer_code=req.offer_code.upper() if req.offer_code else None,
            )
        else:
            raise BadRequestException(
                message=f"Unsupported target type '{req.target_type}'",
                code=ErrorCode.BAD_REQUEST,
            )

        # 5. Handle Zero-Payable (Package Credit or 100% coupon)
        payment_id = str(uuid.uuid4())
        now = utc_now()
        if pricing_snapshot.payable_amount_minor == 0:
            payment = PaymentInDB(
                id=payment_id,
                user_id=caller.id,
                target_type=req.target_type,
                target_id=req.target_id,
                amount_minor=0,
                currency=pricing_snapshot.currency,
                status=PaymentStatus.PAID,
                provider=PaymentProviderName.MOCK,
                payment_method=PaymentMethod.PACKAGE_REDEMPTION
                if pricing_snapshot.user_package_id
                else PaymentMethod.MOCK,
                pricing=pricing_snapshot,
                idempotency_key=req.idempotency_key,
                paid_at=now,
                created_at=now,
                updated_at=now,
            )
            saved = await self.payment_repo.create_payment(payment)
            # Execute commercial fulfillment immediately
            await self._fulfill_commercial_transaction(saved, caller)
            return PaymentResponse.from_db(saved)

        # 6. Gateway Order generation
        order_res = await self.provider.create_order(
            amount_minor=pricing_snapshot.payable_amount_minor,
            currency=pricing_snapshot.currency,
            receipt=payment_id,
            notes={"user_id": caller.id, "target_id": req.target_id},
        )

        payment = PaymentInDB(
            id=payment_id,
            user_id=caller.id,
            target_type=req.target_type,
            target_id=req.target_id,
            amount_minor=pricing_snapshot.payable_amount_minor,
            currency=pricing_snapshot.currency,
            status=PaymentStatus.CREATED,
            provider=self.provider.name,
            provider_order_id=order_res.provider_order_id,
            pricing=pricing_snapshot,
            idempotency_key=req.idempotency_key,
            created_at=now,
            updated_at=now,
        )
        saved = await self.payment_repo.create_payment(payment)
        return PaymentResponse.from_db(saved)

    async def verify_payment(
        self, caller: UserInDB, payment_id: str, req: VerifyPaymentRequest
    ) -> PaymentResponse:
        """Client-driven payment verification and atomic commercial fulfillment."""
        payment = await self.payment_repo.get_by_id(payment_id)
        if not payment:
            raise NotFoundException(
                message="Payment record not found",
                code=ErrorCode.PAYMENT_NOT_FOUND,
            )
        if payment.user_id != caller.id:
            raise ForbiddenException(
                message="Payment belongs to another user",
                code=ErrorCode.PAYMENT_FORBIDDEN,
            )

        # Idempotency check: if already verified, check fulfillment status
        if payment.status == PaymentStatus.PAID:
            if payment.fulfillment_status != FulfillmentStatus.FULFILLED:
                await self._fulfill_commercial_transaction(payment, caller)
                refreshed = await self.payment_repo.get_by_id(payment.id)
                return PaymentResponse.from_db(refreshed or payment)
            return PaymentResponse.from_db(payment)

        # 1. Cryptographic signature check
        is_valid = self.provider.verify_payment_signature(
            order_id=req.provider_order_id,
            payment_id=req.provider_payment_id,
            signature=req.provider_signature,
        )
        if not is_valid:
            await self.payment_repo.mark_payment_failed(
                payment_id=payment.id,
                failure_code="SIGNATURE_MISMATCH",
                failure_message="Payment signature verification failed",
            )
            raise BadRequestException(
                message="Payment signature verification failed",
                code=ErrorCode.PAYMENT_VERIFICATION_FAILED,
            )

        # 2. Atomic state transition to PAID
        paid_payment = await self.payment_repo.mark_payment_paid(
            payment_id=payment.id,
            provider_payment_id=req.provider_payment_id,
            provider_signature=req.provider_signature,
            payment_method=req.payment_method,
        )
        if not paid_payment:
            # Re-read in case concurrent webhook already marked it paid
            latest = await self.payment_repo.get_by_id(payment.id)
            if latest and latest.status == PaymentStatus.PAID:
                if latest.fulfillment_status != FulfillmentStatus.FULFILLED:
                    await self._fulfill_commercial_transaction(latest, caller)
                    refreshed = await self.payment_repo.get_by_id(latest.id)
                    return PaymentResponse.from_db(refreshed or latest)
                return PaymentResponse.from_db(latest)
            raise ConflictException(
                message="Unable to mark payment as paid due to invalid status transition",
                code=ErrorCode.CONFLICT,
            )

        # 3. Commercial fulfillment
        await self._fulfill_commercial_transaction(paid_payment, caller)
        refreshed_final = await self.payment_repo.get_by_id(paid_payment.id)
        return PaymentResponse.from_db(refreshed_final or paid_payment)

    async def process_webhook(self, payload_bytes: bytes, signature_header: str) -> bool:
        """Authoritative webhook verification and state convergence."""
        # 1. Verify signature against configured webhook secret
        secret = self.settings.payment_webhook_secret
        if not self.provider.verify_webhook_signature(payload_bytes, signature_header, secret):
            raise BadRequestException(
                message="Invalid webhook signature",
                code=ErrorCode.PAYMENT_WEBHOOK_INVALID,
            )

        import json
        data = json.loads(payload_bytes.decode("utf-8"))
        order_id = data.get("provider_order_id")
        payment_id_ext = data.get("provider_payment_id")
        event = data.get("event")

        if not order_id:
            return False

        payment = await self.payment_repo.get_by_provider_order_id(order_id)
        if not payment:
            return False

        if payment.status == PaymentStatus.PAID:
            if payment.fulfillment_status != FulfillmentStatus.FULFILLED:
                user = await self.booking_repo.bookings.database["users"].find_one(
                    {"id": payment.user_id}
                )
                if user:
                    caller = UserInDB(**user)
                    await self._fulfill_commercial_transaction(payment, caller)
            return True  # Idempotent return

        if event in ("payment.captured", "order.paid", "payment_success"):
            paid_payment = await self.payment_repo.mark_payment_paid(
                payment_id=payment.id,
                provider_payment_id=payment_id_ext or "webhook_verified",
            )
            if paid_payment:
                # Fulfill commercial action
                user = await self.booking_repo.bookings.database["users"].find_one(
                    {"id": payment.user_id}
                )
                if user:
                    caller = UserInDB(**user)
                    await self._fulfill_commercial_transaction(paid_payment, caller)
            return True
        elif event in ("payment.failed", "payment_failed"):
            await self.payment_repo.mark_payment_failed(
                payment_id=payment.id,
                failure_code="GATEWAY_FAILED",
                failure_message=data.get("failure_message", "Payment failed at gateway"),
            )
            return True

        return False

    async def _fulfill_commercial_transaction(
        self, payment: PaymentInDB, caller: UserInDB
    ) -> None:
        """Grant commercial asset: confirm booking or allocate user package balance."""
        if payment.fulfillment_status == FulfillmentStatus.FULFILLED:
            return

        await self.payment_repo.update_fulfillment_status(
            payment.id, FulfillmentStatus.PROCESSING
        )
        try:
            # A. Record offer usage if coupon applied
            if payment.pricing.offer_code:
                offer = await self.offer_service.offer_repo.get_by_code(payment.pricing.offer_code)
                if offer:
                    await self.offer_service.record_usage_atomic(offer.id, caller.id)

            # B. Consume package credit if session balance was used
            if payment.pricing.user_package_id:
                await self.package_service.consume_session_for_booking(
                    user_pkg_id=payment.pricing.user_package_id, user_id=caller.id
                )

            # C. Target fulfillment
            if payment.target_type == PaymentTargetType.BOOKING:
                # Confirm reservation into booking using Phase 5 service
                await self.booking_service.confirm_booking(
                    caller=caller,
                    req=ConfirmBookingRequest(reservation_id=payment.target_id),
                )
            elif payment.target_type == PaymentTargetType.PACKAGE:
                # Allocate user package
                await self.package_service.fulfill_package_purchase(
                    user_id=caller.id,
                    product_id=payment.target_id,
                    payment_id=payment.id,
                )

            await self.payment_repo.update_fulfillment_status(
                payment.id, FulfillmentStatus.FULFILLED
            )
        except Exception:
            await self.payment_repo.update_fulfillment_status(
                payment.id, FulfillmentStatus.FAILED
            )
            raise

    async def get_payment(self, caller: UserInDB, payment_id: str) -> PaymentResponse:
        payment = await self.payment_repo.get_by_id(payment_id)
        if not payment:
            raise NotFoundException(
                message="Payment not found",
                code=ErrorCode.PAYMENT_NOT_FOUND,
            )
        if payment.user_id != caller.id:
            raise ForbiddenException(
                message="Payment belongs to another user",
                code=ErrorCode.PAYMENT_FORBIDDEN,
            )
        return PaymentResponse.from_db(payment)
