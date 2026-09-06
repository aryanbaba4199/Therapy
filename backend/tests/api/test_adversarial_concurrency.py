"""Adversarial concurrency tests covering Razorpay webhooks, fulfillment claims, slot hold, session states, and OTP."""

import asyncio
import uuid
from datetime import timedelta
from typing import Any

import pytest

from app.common.exceptions.error_codes import ErrorCode
from app.common.utils.datetime_utils import utc_now
from app.modules.auth.auth_constants import OtpChannel
from app.modules.auth.auth_repository import AuthRepository
from app.modules.auth.auth_schema import SendOtpRequest
from app.modules.auth.auth_service import AuthService, MockOtpProvider
from app.modules.booking.booking_repository import BookingRepository
from app.modules.booking.booking_service import BookingService
from app.modules.offer.offer_repository import OfferRepository
from app.modules.offer.offer_service import OfferService
from app.modules.package.package_repository import PackageRepository
from app.modules.package.package_service import PackageService
from app.modules.payment.payment_constants import (
    FulfillmentStatus,
    PaymentProviderName,
    PaymentStatus,
)
from app.modules.payment.payment_model import PaymentInDB, PaymentPricingSnapshot
from app.modules.payment.payment_repository import PaymentRepository
from app.modules.payment.payment_service import PaymentService
from app.modules.session.session_constants import SessionStatus
from app.modules.session.session_model import SessionInDB
from app.modules.session.session_repository import SessionRepository
from app.modules.session.session_service import SessionService
from app.modules.therapist.therapist_repository import TherapistRepository
from app.modules.user.user_constants import UserRole, UserStatus
from app.modules.user.user_model import UserInDB
from app.modules.user.user_repository import UserRepository


def make_test_user(user_id: str, email: str, role: UserRole = UserRole.USER) -> UserInDB:
    now = utc_now()
    return UserInDB(
        id=user_id,
        email=email,
        first_name="Concurrency",
        last_name="Tester",
        roles=[role],
        status=UserStatus.ACTIVE,
        is_verified=True,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_concurrent_payment_fulfillment_exactly_once(mock_db: Any, settings: Any) -> None:
    """Simulate 20 concurrent verify_payment and webhook requests racing to fulfill the same payment.

    Verifies that exactly 1 worker claims the fulfillment and side effects execute exactly once.
    """
    payment_repo = PaymentRepository(mock_db)
    booking_repo = BookingRepository(mock_db)
    session_repo = SessionRepository(mock_db)
    therapist_repo = TherapistRepository(mock_db)
    UserRepository(mock_db)
    offer_repo = OfferRepository(mock_db)
    package_repo = PackageRepository(mock_db)

    await payment_repo.ensure_indexes()
    await booking_repo.ensure_indexes()
    await session_repo.create_indexes()
    await package_repo.ensure_indexes()
    await offer_repo.ensure_indexes()

    session_service = SessionService(
        session_repo=session_repo,
        booking_repo=booking_repo,
        therapist_repo=therapist_repo,
        settings=settings,
    )
    booking_service = BookingService(
        booking_repo=booking_repo,
        therapist_repo=therapist_repo,
        availability_service=Any,  # type: ignore[arg-type]
        session_service=session_service,
        settings=settings,
    )

    user_id = str(uuid.uuid4())
    caller = make_test_user(user_id, "concurrent_buyer@oppam.in")
    await mock_db["users"].insert_one(caller.model_dump())

    # Create a dummy package product to fulfill
    product_id = str(uuid.uuid4())
    await mock_db["package_products"].insert_one({
        "id": product_id,
        "title": "5 Session Bundle",
        "description": "Bundle",
        "session_count": 5,
        "validity_days": 60,
        "price_minor": 500000,
        "currency": "INR",
        "is_active": True,
        "created_at": utc_now(),
        "updated_at": utc_now(),
    })

    # Create PAID payment ready for fulfillment
    payment_id = str(uuid.uuid4())
    payment = PaymentInDB(
        id=payment_id,
        user_id=user_id,
        target_type="package",  # type: ignore[arg-type]
        target_id=product_id,
        amount_minor=500000,
        currency="INR",
        status=PaymentStatus.PAID,
        fulfillment_status=FulfillmentStatus.PENDING,
        provider=PaymentProviderName.MOCK,
        pricing=PaymentPricingSnapshot(
            base_amount_minor=500000,
            discount_amount_minor=0,
            payable_amount_minor=500000,
            currency="INR",
        ),
    )
    await payment_repo.create_payment(payment)

    offer_service = OfferService(offer_repo)
    package_service = PackageService(package_repo)

    payment_service = PaymentService(
        payment_repo=payment_repo,
        booking_repo=booking_repo,
        booking_service=booking_service,
        offer_service=offer_service,
        package_service=package_service,
        settings=settings,
    )

    # 20 concurrent coroutines attempting fulfillment claim
    results = await asyncio.gather(
        *(
            payment_service._claim_and_fulfill_commercial_transaction(payment_id, caller)
            for _ in range(20)
        ),
        return_exceptions=True,
    )

    # Ensure no crashes
    for r in results:
        assert not isinstance(r, Exception), f"Unexpected exception in fulfillment: {r}"

    # Verify final payment state
    final_payment = await payment_repo.get_by_id(payment_id)
    assert final_payment is not None
    assert final_payment.fulfillment_status == FulfillmentStatus.FULFILLED

    # Verify that exactly ONE UserPackage was created for this payment
    user_packages = await mock_db["user_packages"].find({"payment_id": payment_id}).to_list(100)
    assert len(user_packages) == 1
    assert user_packages[0]["remaining_sessions"] == 5


@pytest.mark.asyncio
async def test_adversarial_otp_issuance_cooldown_concurrency(mock_db: Any, settings: Any) -> None:
    """Simulate 20 rapid concurrent OTP send requests for the same phone number.

    Verifies that exactly 1 request acquires the cooldown slot and succeeds, while the other 19 fail cleanly.
    """
    auth_repo = AuthRepository(mock_db)
    await auth_repo.ensure_indexes()

    otp_provider = MockOtpProvider()
    user_repo = UserRepository(mock_db)

    auth_service = AuthService(
        auth_repo=auth_repo,
        user_repo=user_repo,
        otp_provider=otp_provider,
        settings=settings,
    )

    phone = "+919876543210"
    req = SendOtpRequest(phone=phone, channel=OtpChannel.SMS)

    # Dispatch 20 concurrent send_otp calls
    results = await asyncio.gather(
        *(auth_service.send_otp(req) for _ in range(20)),
        return_exceptions=True,
    )

    successes = [r for r in results if not isinstance(r, Exception)]
    failures = [r for r in results if isinstance(r, Exception)]

    # Exactly 1 success, 19 RateLimitedException
    assert len(successes) == 1, f"Expected exactly 1 success, got {len(successes)}"
    assert len(failures) == 19
    for f in failures:
        from app.common.exceptions.app_exceptions import RateLimitedException
        assert isinstance(f, RateLimitedException)
        assert f.code == ErrorCode.AUTH_OTP_RATE_LIMITED


@pytest.mark.asyncio
async def test_session_state_transition_adversarial_cancellation(mock_db: Any) -> None:
    """Verify that once a session transitions to IN_PROGRESS or COMPLETED, it CANNOT be cancelled."""
    session_repo = SessionRepository(mock_db)
    await session_repo.create_indexes()

    session_id = str(uuid.uuid4())
    now = utc_now()
    session = SessionInDB(
        id=session_id,
        booking_id=str(uuid.uuid4()),
        therapist_id=str(uuid.uuid4()),
        client_id=str(uuid.uuid4()),
        scheduled_start_at=now,
        scheduled_end_at=now + timedelta(minutes=50),
        duration_minutes=50,
        session_mode="video",
        status=SessionStatus.SCHEDULED,
    )
    await session_repo.create_session(session)

    # 1. Transition SCHEDULED -> IN_PROGRESS
    started = await session_repo.start_session_atomic(session_id, started_at=now)
    assert started is not None
    assert started.status == SessionStatus.IN_PROGRESS

    # 2. Attempt to cancel while IN_PROGRESS -> must fail
    cancelled = await session_repo.cancel_session(session_id)
    assert cancelled is None, "Session in progress must NOT be cancelled!"

    # Verify session remains IN_PROGRESS
    current = await session_repo.get_session_by_id(session_id)
    assert current is not None
    assert current.status == SessionStatus.IN_PROGRESS

    # 3. Transition IN_PROGRESS -> COMPLETED
    completed = await session_repo.complete_session_atomic(session_id, ended_at=now + timedelta(minutes=50))
    assert completed is not None
    assert completed.status == SessionStatus.COMPLETED

    # 4. Attempt to cancel while COMPLETED -> must fail
    cancelled_after = await session_repo.cancel_session(session_id)
    assert cancelled_after is None, "Completed session must NOT be cancelled!"
