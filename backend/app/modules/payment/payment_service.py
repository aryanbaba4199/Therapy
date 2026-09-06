"""Domain business logic for Payment initiation, verification, and fulfillment."""

import hashlib
import json
import logging
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
    WebhookEventStatus,
)
from app.modules.payment.payment_model import PaymentInDB, PaymentPricingSnapshot
from app.modules.payment.payment_provider import MockPaymentProvider, PaymentProvider
from app.modules.payment.payment_repository import PaymentRepository
from app.modules.payment.payment_schema import (
    CreatePaymentRequest,
    PaymentConfigResponse,
    PaymentResponse,
    VerifyPaymentRequest,
)
from app.modules.payment.payment_webhook_model import PaymentWebhookEventInDB
from app.modules.user.user_model import UserInDB

logger = logging.getLogger(__name__)


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

    def get_public_config(self) -> PaymentConfigResponse:
        """Expose client-safe payment gateway configuration."""
        return PaymentConfigResponse(
            payment_provider=self.settings.payment_provider,
            razorpay_key_id=self.settings.razorpay_key_id,
            razorpay_account_mode=self.settings.razorpay_account_mode,
        )

    async def _build_payment_response(self, payment: PaymentInDB) -> PaymentResponse:
        booking_id = None
        if payment.target_type == PaymentTargetType.BOOKING:
            booking = await self.booking_repo.get_booking_by_reservation_id(payment.target_id)
            if booking:
                booking_id = booking.id
        return PaymentResponse.from_db(payment, booking_id=booking_id)

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
                return await self._build_payment_response(existing)

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
            # Fulfill commercial action atomically
            await self._claim_and_fulfill_commercial_transaction(saved.id, caller)
            refreshed = await self.payment_repo.get_by_id(saved.id)
            return await self._build_payment_response(refreshed or saved)

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
        return await self._build_payment_response(saved)

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

        # Security check: client provider_order_id must match stored provider_order_id
        if payment.provider_order_id and req.provider_order_id != payment.provider_order_id:
            raise BadRequestException(
                message="Provider order ID does not match payment intent",
                code=ErrorCode.PAYMENT_VERIFICATION_FAILED,
            )

        # Idempotency check: if already marked PAID
        if payment.status == PaymentStatus.PAID:
            if payment.fulfillment_status != FulfillmentStatus.FULFILLED:
                await self._claim_and_fulfill_commercial_transaction(payment.id, caller)
            refreshed = await self.payment_repo.get_by_id(payment.id)
            return await self._build_payment_response(refreshed or payment)

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
                    await self._claim_and_fulfill_commercial_transaction(latest.id, caller)
                refreshed = await self.payment_repo.get_by_id(latest.id)
                return await self._build_payment_response(refreshed or latest)
            raise ConflictException(
                message="Unable to mark payment as paid due to invalid status transition",
                code=ErrorCode.CONFLICT,
            )

        # 3. Commercial fulfillment through atomic claim engine
        await self._claim_and_fulfill_commercial_transaction(paid_payment.id, caller)
        refreshed_final = await self.payment_repo.get_by_id(paid_payment.id)
        return await self._build_payment_response(refreshed_final or paid_payment)

    async def process_webhook(self, payload_bytes: bytes, signature_header: str) -> bool:
        """Authoritative webhook verification, event deduplication, and atomic fulfillment."""
        # 1. Verify signature against configured webhook secret
        secret = (
            self.settings.razorpay_webhook_secret
            if self.provider.name == PaymentProviderName.RAZORPAY
            else self.settings.payment_webhook_secret
        )
        if not self.provider.verify_webhook_signature(payload_bytes, signature_header, secret):
            raise BadRequestException(
                message="Invalid webhook signature",
                code=ErrorCode.PAYMENT_WEBHOOK_INVALID,
            )

        try:
            data = json.loads(payload_bytes.decode("utf-8"))
        except Exception as exc:
            raise BadRequestException(
                message="Invalid JSON webhook payload",
                code=ErrorCode.PAYMENT_WEBHOOK_INVALID,
            ) from exc

        # Extract event info for Razorpay and Mock providers
        event_type = ""
        provider_order_id = ""
        provider_payment_id = ""
        event_id = ""

        if self.provider.name == PaymentProviderName.RAZORPAY or "contains" in data or "payload" in data:
            # Razorpay standard webhook structure
            event_type = data.get("event", "")
            payload_entity = data.get("payload", {})
            payment_entity = payload_entity.get("payment", {}).get("entity", {})
            order_entity = payload_entity.get("order", {}).get("entity", {})
            provider_order_id = payment_entity.get("order_id") or order_entity.get("id") or data.get("provider_order_id") or ""
            provider_payment_id = payment_entity.get("id") or data.get("provider_payment_id") or ""
            event_id = data.get("id") or data.get("event_id") or f"evt_rzp_{provider_payment_id or uuid.uuid4().hex[:12]}"
        else:
            # Mock or simplified format
            event_type = data.get("event", "")
            provider_order_id = data.get("provider_order_id", "")
            provider_payment_id = data.get("provider_payment_id", "")
            event_id = data.get("event_id") or f"evt_mock_{provider_payment_id or uuid.uuid4().hex[:12]}"

        # 2. Webhook Event Deduplication using payment_webhook_events
        payload_hash = hashlib.sha256(payload_bytes).hexdigest()
        webhook_event = PaymentWebhookEventInDB(
            id=str(uuid.uuid4()),
            provider=self.provider.name,
            event_id=event_id,
            event_type=event_type,
            payload_hash=payload_hash,
            status=WebhookEventStatus.PENDING,
        )
        is_new_event = await self.payment_repo.record_webhook_event(webhook_event)
        if not is_new_event:
            logger.info("Ignoring duplicate webhook event %s (%s)", event_id, event_type)
            return True

        try:
            if not provider_order_id:
                await self.payment_repo.update_webhook_event_status(
                    event_id=event_id,
                    provider=self.provider.name,
                    status=WebhookEventStatus.PROCESSED,
                )
                return False

            payment = await self.payment_repo.get_by_provider_order_id(provider_order_id)
            if not payment:
                await self.payment_repo.update_webhook_event_status(
                    event_id=event_id,
                    provider=self.provider.name,
                    status=WebhookEventStatus.PROCESSED,
                    error_message=f"No payment record found for order {provider_order_id}",
                )
                return False

            # Resolve caller user for fulfillment
            user_doc = await self.booking_repo.bookings.database["users"].find_one(
                {"id": payment.user_id}
            )
            caller = UserInDB(**user_doc) if user_doc else None

            # Handle event types
            success_events = (
                "payment.captured",
                "order.paid",
                "payment_success",
                "payment.authorized",
            )
            failure_events = (
                "payment.failed",
                "payment_failed",
            )

            if event_type in success_events:
                if payment.status != PaymentStatus.PAID:
                    paid_payment = await self.payment_repo.mark_payment_paid(
                        payment_id=payment.id,
                        provider_payment_id=provider_payment_id or "webhook_captured",
                    )
                    if paid_payment and caller:
                        await self._claim_and_fulfill_commercial_transaction(paid_payment.id, caller)
                elif caller and payment.fulfillment_status != FulfillmentStatus.FULFILLED:
                    await self._claim_and_fulfill_commercial_transaction(payment.id, caller)

                await self.payment_repo.update_webhook_event_status(
                    event_id=event_id,
                    provider=self.provider.name,
                    status=WebhookEventStatus.PROCESSED,
                )
                return True

            elif event_type in failure_events:
                await self.payment_repo.mark_payment_failed(
                    payment_id=payment.id,
                    failure_code="GATEWAY_FAILED",
                    failure_message=data.get("failure_message", "Payment failed at gateway"),
                )
                await self.payment_repo.update_webhook_event_status(
                    event_id=event_id,
                    provider=self.provider.name,
                    status=WebhookEventStatus.PROCESSED,
                )
                return True

            await self.payment_repo.update_webhook_event_status(
                event_id=event_id,
                provider=self.provider.name,
                status=WebhookEventStatus.PROCESSED,
            )
            return False

        except Exception as exc:
            logger.exception("Error processing webhook event %s: %s", event_id, exc)
            await self.payment_repo.update_webhook_event_status(
                event_id=event_id,
                provider=self.provider.name,
                status=WebhookEventStatus.FAILED,
                error_message=str(exc),
            )
            raise

    async def _claim_and_fulfill_commercial_transaction(
        self, payment_id: str, caller: UserInDB
    ) -> None:
        """Atomically claim fulfillment rights and execute commercial side effects exactly once."""
        payment = await self.payment_repo.get_by_id(payment_id)
        if not payment:
            return

        if payment.fulfillment_status == FulfillmentStatus.FULFILLED:
            return

        worker_id = f"worker_{uuid.uuid4().hex[:8]}"
        claimed = await self.payment_repo.claim_fulfillment_ownership(
            payment_id=payment.id, worker_id=worker_id, stale_timeout_seconds=60
        )
        if not claimed:
            # Another worker claimed or fulfillment already succeeded
            return

        try:
            # A. Record offer usage if coupon applied (idempotent per payment_id)
            if payment.pricing.offer_code:
                offer = await self.offer_service.offer_repo.get_by_code(payment.pricing.offer_code)
                if offer:
                    await self.offer_service.record_usage_atomic(
                        offer_id=offer.id, user_id=caller.id, payment_id=payment.id
                    )

            # B. Consume package credit if session balance was used (idempotent per payment_id)
            if payment.pricing.user_package_id:
                await self.package_service.consume_session_for_booking(
                    user_pkg_id=payment.pricing.user_package_id,
                    user_id=caller.id,
                    payment_id=payment.id,
                )

            # C. Target fulfillment
            if payment.target_type == PaymentTargetType.BOOKING:
                await self.booking_service.confirm_booking(
                    caller=caller,
                    req=ConfirmBookingRequest(reservation_id=payment.target_id),
                )
            elif payment.target_type == PaymentTargetType.PACKAGE:
                await self.package_service.fulfill_package_purchase(
                    user_id=caller.id,
                    product_id=payment.target_id,
                    payment_id=payment.id,
                )

            await self.payment_repo.mark_fulfillment_success(payment.id)
        except Exception as exc:
            logger.exception("Fulfillment failed for payment %s: %s", payment.id, exc)
            await self.payment_repo.mark_fulfillment_failed(payment.id, str(exc))
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
        return await self._build_payment_response(payment)
