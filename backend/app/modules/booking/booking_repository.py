"""Database repository for Reservation and Booking entities in MongoDB."""

from datetime import UTC, datetime
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.utils.datetime_utils import utc_now
from app.modules.booking.booking_constants import BookingStatus, ReservationStatus
from app.modules.booking.booking_model import BookingInDB, ReservationInDB


class BookingRepository:
    """Encapsulates MongoDB collections and queries for reservations and bookings."""

    RESERVATIONS_COLLECTION = "reservations"
    BOOKINGS_COLLECTION = "bookings"

    def __init__(self, db: AsyncIOMotorDatabase[dict[str, Any]]) -> None:
        self.reservations = db[self.RESERVATIONS_COLLECTION]
        self.bookings = db[self.BOOKINGS_COLLECTION]

    async def ensure_indexes(self) -> None:
        """Create query and uniqueness constraints for concurrency protection."""
        # Reservations indexes
        await self.reservations.create_indexes([
            IndexModel(
                [("therapist_id", ASCENDING), ("slot_id", ASCENDING)],
                unique=True,
                partialFilterExpression={"status": ReservationStatus.ACTIVE.value},
                name="idx_unique_active_reservation",
            ),
            IndexModel(
                [("client_id", ASCENDING), ("created_at", DESCENDING)],
                name="idx_reservation_client",
            ),
            IndexModel([("expires_at", ASCENDING)], name="idx_reservation_expiry"),
            IndexModel([("id", ASCENDING)], unique=True, name="idx_reservation_id"),
        ])

        # Bookings indexes
        await self.bookings.create_indexes([
            IndexModel(
                [("therapist_id", ASCENDING), ("slot_id", ASCENDING)],
                unique=True,
                partialFilterExpression={
                    "status": {"$in": [BookingStatus.PENDING.value, BookingStatus.CONFIRMED.value]}
                },
                name="idx_unique_active_booking",
            ),
            IndexModel(
                [("client_id", ASCENDING), ("start_at", DESCENDING)],
                name="idx_booking_client_start",
            ),
            IndexModel(
                [("therapist_id", ASCENDING), ("start_at", DESCENDING)],
                name="idx_booking_therapist_start",
            ),
            IndexModel(
                [("reservation_id", ASCENDING)],
                unique=True,
                name="idx_booking_reservation_id",
            ),
            IndexModel([("id", ASCENDING)], unique=True, name="idx_booking_id"),
        ])

    async def create_reservation(self, reservation: ReservationInDB) -> ReservationInDB:
        """Insert new reservation. Raises DuplicateKeyError on concurrent collisions."""
        await self.reservations.insert_one(reservation.model_dump())
        return reservation

    async def get_reservation_by_id(self, reservation_id: str) -> ReservationInDB | None:
        """Fetch reservation by UUID."""
        doc = await self.reservations.find_one({"id": reservation_id})
        return ReservationInDB(**doc) if doc else None

    async def get_active_reservation_for_slot(
        self, therapist_id: str, slot_id: str
    ) -> ReservationInDB | None:
        """Fetch active reservation for a therapist slot."""
        doc = await self.reservations.find_one({
            "therapist_id": therapist_id,
            "slot_id": slot_id,
            "status": ReservationStatus.ACTIVE.value,
        })
        return ReservationInDB(**doc) if doc else None

    async def update_reservation_status(
        self, reservation_id: str, status: ReservationStatus
    ) -> ReservationInDB | None:
        """Update reservation status and timestamp."""
        res = await self.reservations.find_one_and_update(
            {"id": reservation_id},
            {"$set": {"status": status.value, "updated_at": utc_now()}},
            return_document=True,
        )
        return ReservationInDB(**res) if res else None

    async def create_booking(self, booking: BookingInDB) -> BookingInDB:
        """Insert new confirmed booking."""
        await self.bookings.insert_one(booking.model_dump())
        return booking

    async def get_booking_by_id(self, booking_id: str) -> BookingInDB | None:
        """Fetch booking by UUID."""
        doc = await self.bookings.find_one({"id": booking_id})
        return BookingInDB(**doc) if doc else None

    async def get_booking_by_reservation_id(self, reservation_id: str) -> BookingInDB | None:
        """Fetch booking created from a specific reservation ID."""
        doc = await self.bookings.find_one({"reservation_id": reservation_id})
        return BookingInDB(**doc) if doc else None

    async def find_client_bookings(
        self,
        client_id: str,
        status_filter: list[BookingStatus] | None = None,
        skip: int = 0,
        limit: int = 10,
    ) -> tuple[list[BookingInDB], int]:
        """Paginated search for a client's bookings."""
        query: dict[str, Any] = {"client_id": client_id}
        if status_filter:
            query["status"] = {"$in": [s.value for s in status_filter]}

        total = await self.bookings.count_documents(query)
        cursor = self.bookings.find(query).sort("start_at", DESCENDING).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [BookingInDB(**d) for d in docs], total

    async def find_therapist_bookings(
        self,
        therapist_id: str,
        status_filter: list[BookingStatus] | None = None,
        skip: int = 0,
        limit: int = 10,
    ) -> tuple[list[BookingInDB], int]:
        """Paginated search for a therapist's bookings."""
        query: dict[str, Any] = {"therapist_id": therapist_id}
        if status_filter:
            query["status"] = {"$in": [s.value for s in status_filter]}

        total = await self.bookings.count_documents(query)
        cursor = self.bookings.find(query).sort("start_at", DESCENDING).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        return [BookingInDB(**d) for d in docs], total

    async def update_booking_status(
        self,
        booking_id: str,
        status: BookingStatus,
        cancellation_reason: str | None = None,
        cancelled_by: str | None = None,
    ) -> BookingInDB | None:
        """Update booking lifecycle status."""
        updates: dict[str, Any] = {
            "status": status.value,
            "updated_at": utc_now(),
        }
        if status == BookingStatus.CANCELLED:
            updates["cancellation_reason"] = cancellation_reason
            updates["cancelled_by"] = cancelled_by
            updates["cancelled_at"] = utc_now()

        res = await self.bookings.find_one_and_update(
            {"id": booking_id},
            {"$set": updates},
            return_document=True,
        )
        return BookingInDB(**res) if res else None

    async def get_active_reserved_or_booked_slot_ids(
        self, therapist_id: str, start_range: datetime, end_range: datetime
    ) -> set[str]:
        """Collect all slot IDs that are currently actively reserved or booked."""
        now = datetime.now(UTC)
        slot_ids: set[str] = set()

        # 1. Query active reservations that have not yet expired
        res_cursor = self.reservations.find({
            "therapist_id": therapist_id,
            "status": ReservationStatus.ACTIVE.value,
            "expires_at": {"$gt": now},
            "start_at": {"$gte": start_range, "$lte": end_range},
        }, {"slot_id": 1})
        res_docs = await res_cursor.to_list(length=500)
        for d in res_docs:
            if "slot_id" in d:
                slot_ids.add(d["slot_id"])

        # 2. Query confirmed / pending bookings
        book_cursor = self.bookings.find({
            "therapist_id": therapist_id,
            "status": {"$in": [BookingStatus.PENDING.value, BookingStatus.CONFIRMED.value]},
            "start_at": {"$gte": start_range, "$lte": end_range},
        }, {"slot_id": 1})
        book_docs = await book_cursor.to_list(length=500)
        for d in book_docs:
            if "slot_id" in d:
                slot_ids.add(d["slot_id"])

        return slot_ids
