"""Booking and reservation factories for deterministic test data."""

import uuid
from datetime import timedelta
from typing import Any

from app.common.utils.datetime_utils import utc_now
from app.modules.booking.booking_constants import BookingStatus, ReservationStatus
from app.modules.booking.booking_model import (
    BookingInDB,
    ClientSnapshot,
    PricingSnapshot,
    ReservationInDB,
    TherapistSnapshot,
)
from app.modules.therapist.therapist_constants import SessionMode


class BookingFactory:
    @staticmethod
    def build_reservation(
        *,
        id: str | None = None,
        therapist_id: str | None = None,
        client_id: str | None = None,
        slot_id: str | None = None,
        start_at: Any | None = None,
        duration_minutes: int = 60,
        session_mode: SessionMode = SessionMode.ONLINE,
        status: ReservationStatus = ReservationStatus.ACTIVE,
        ttl_minutes: int = 15,
    ) -> ReservationInDB:
        r_id = id or str(uuid.uuid4())
        t_id = therapist_id or str(uuid.uuid4())
        c_id = client_id or str(uuid.uuid4())
        s_id = slot_id or str(uuid.uuid4())
        now = utc_now()
        slot_start = start_at or (now + timedelta(days=1))
        slot_end = slot_start + timedelta(minutes=duration_minutes)

        return ReservationInDB(
            id=r_id,
            therapist_id=t_id,
            client_id=c_id,
            slot_id=s_id,
            start_at=slot_start,
            end_at=slot_end,
            duration_minutes=duration_minutes,
            session_mode=session_mode,
            status=status,
            reserved_at=now,
            expires_at=now + timedelta(minutes=ttl_minutes),
            created_at=now,
            updated_at=now,
        )

    @staticmethod
    async def create_reservation(mock_db: Any, **kwargs: Any) -> ReservationInDB:
        res = BookingFactory.build_reservation(**kwargs)
        await mock_db["reservations"].insert_one(res.model_dump(mode="json"))
        return res

    @staticmethod
    def build_booking(
        *,
        id: str | None = None,
        reservation_id: str | None = None,
        therapist_id: str | None = None,
        client_id: str | None = None,
        slot_id: str | None = None,
        start_at: Any | None = None,
        duration_minutes: int = 60,
        amount: float = 1500.0,
        currency: str = "INR",
        session_mode: SessionMode = SessionMode.ONLINE,
        status: BookingStatus = BookingStatus.CONFIRMED,
        therapist_name: str = "Dr. Anita Menon",
        client_name: str = "Rahul Nair",
    ) -> BookingInDB:
        b_id = id or str(uuid.uuid4())
        r_id = reservation_id or str(uuid.uuid4())
        t_id = therapist_id or str(uuid.uuid4())
        c_id = client_id or str(uuid.uuid4())
        s_id = slot_id or str(uuid.uuid4())
        now = utc_now()
        slot_start = start_at or (now + timedelta(days=1))
        slot_end = slot_start + timedelta(minutes=duration_minutes)

        return BookingInDB(
            id=b_id,
            reservation_id=r_id,
            therapist_id=t_id,
            client_id=c_id,
            slot_id=s_id,
            start_at=slot_start,
            end_at=slot_end,
            duration_minutes=duration_minutes,
            session_mode=session_mode,
            status=status,
            pricing=PricingSnapshot(amount=amount, currency=currency, duration_minutes=duration_minutes),
            therapist=TherapistSnapshot(
                id=t_id,
                display_name=therapist_name,
                designation="Clinical Psychologist",
                specialization="clinical_psychologist",
            ),
            client=ClientSnapshot(
                id=c_id,
                first_name=client_name.split()[0],
                last_name=client_name.split()[-1] if " " in client_name else "",
            ),
            created_at=now,
            updated_at=now,
        )

    @staticmethod
    async def create_booking(mock_db: Any, **kwargs: Any) -> BookingInDB:
        booking = BookingFactory.build_booking(**kwargs)
        await mock_db["bookings"].insert_one(booking.model_dump(mode="json"))
        return booking
