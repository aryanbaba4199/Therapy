"""Unit tests to verify test factories integrity and determinism."""

import pytest

from app.modules.booking.booking_constants import BookingStatus, ReservationStatus
from app.modules.payment.payment_constants import FulfillmentStatus, PaymentStatus
from app.modules.session.session_constants import SessionStatus
from app.modules.user.user_constants import UserRole
from tests.factories import (
    BookingFactory,
    PaymentFactory,
    SessionFactory,
    TherapistFactory,
    UserFactory,
)


@pytest.mark.unit
def test_user_factory_build() -> None:
    user = UserFactory.build(first_name="Arun", roles=[UserRole.USER])
    assert user.first_name == "Arun"
    assert user.roles == [UserRole.USER]
    assert user.id is not None
    assert user.email is not None


@pytest.mark.unit
def test_therapist_factory_build() -> None:
    therapist = TherapistFactory.build(display_name="Dr. Maya")
    assert therapist.display_name == "Dr. Maya"
    assert therapist.pricing.currency == "INR"
    assert therapist.verification.status.value == "verified"


@pytest.mark.unit
def test_booking_factory_build() -> None:
    res = BookingFactory.build_reservation()
    assert res.status == ReservationStatus.ACTIVE
    assert res.expires_at > res.start_at or res.expires_at is not None

    booking = BookingFactory.build_booking()
    assert booking.status == BookingStatus.CONFIRMED
    assert booking.pricing.currency == "INR"


@pytest.mark.unit
def test_payment_factory_build() -> None:
    payment = PaymentFactory.build(amount_minor=200000)
    assert payment.amount_minor == 200000
    assert payment.status == PaymentStatus.PENDING
    assert payment.fulfillment_status == FulfillmentStatus.PENDING


@pytest.mark.unit
def test_session_factory_build() -> None:
    session = SessionFactory.build()
    assert session.status == SessionStatus.SCHEDULED
    assert session.meeting is not None
    assert "meet.google.com" in (session.meeting.join_url or "")


@pytest.mark.unit
async def test_factories_persistence(mock_db: pytest.FixtureRequest) -> None:
    user = await UserFactory.create(mock_db)
    found_user = await mock_db["users"].find_one({"id": user.id}) # type: ignore[index]
    assert found_user is not None
    assert found_user["id"] == user.id
