"""Database repository for Availability entities in MongoDB."""

from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, IndexModel

from app.modules.availability.availability_model import (
    DateExceptionInDB,
    ExtraSlotInDB,
    WeeklyScheduleInDB,
)


class AvailabilityRepository:
    """Encapsulates MongoDB collections and queries for therapist availability."""

    SCHEDULES_COLLECTION = "availability_schedules"
    EXCEPTIONS_COLLECTION = "availability_exceptions"
    EXTRA_SLOTS_COLLECTION = "extra_slots"

    def __init__(self, db: AsyncIOMotorDatabase[dict[str, Any]]) -> None:
        self.db = db
        self.schedules = db[self.SCHEDULES_COLLECTION]
        self.exceptions = db[self.EXCEPTIONS_COLLECTION]
        self.extra_slots = db[self.EXTRA_SLOTS_COLLECTION]


    async def ensure_indexes(self) -> None:
        """Create necessary indexes for efficient scheduling lookups."""
        await self.schedules.create_indexes([
            IndexModel([("therapist_id", ASCENDING)], unique=True, name="idx_schedule_therapist_id"),
        ])
        await self.exceptions.create_indexes([
            IndexModel(
                [("therapist_id", ASCENDING), ("date", ASCENDING)],
                unique=True,
                name="idx_exception_therapist_date",
            ),
        ])
        await self.extra_slots.create_indexes([
            IndexModel(
                [("therapist_id", ASCENDING), ("date", ASCENDING)],
                name="idx_extra_slots_therapist_date",
            ),
            IndexModel([("id", ASCENDING)], unique=True, name="idx_extra_slots_id"),
        ])

    async def get_weekly_schedule(self, therapist_id: str) -> WeeklyScheduleInDB | None:
        """Retrieve weekly schedule for a therapist."""
        doc = await self.schedules.find_one({"therapist_id": therapist_id})
        return WeeklyScheduleInDB(**doc) if doc else None

    async def upsert_weekly_schedule(self, schedule: WeeklyScheduleInDB) -> WeeklyScheduleInDB:
        """Insert or replace weekly schedule."""
        await self.schedules.update_one(
            {"therapist_id": schedule.therapist_id},
            {"$set": schedule.model_dump()},
            upsert=True,
        )
        return schedule

    async def delete_weekly_schedule(self, therapist_id: str) -> bool:
        """Remove weekly schedule for a therapist."""
        res = await self.schedules.delete_one({"therapist_id": therapist_id})
        return res.deleted_count > 0

    async def get_exception(self, therapist_id: str, date_str: str) -> DateExceptionInDB | None:
        """Retrieve date-specific exception."""
        doc = await self.exceptions.find_one({"therapist_id": therapist_id, "date": date_str})
        return DateExceptionInDB(**doc) if doc else None

    async def get_exceptions_for_range(
        self, therapist_id: str, start_date: str, end_date: str
    ) -> list[DateExceptionInDB]:
        """Retrieve all exceptions falling within date range [start_date, end_date]."""
        cursor = self.exceptions.find({
            "therapist_id": therapist_id,
            "date": {"$gte": start_date, "$lte": end_date},
        }).sort("date", ASCENDING)
        docs = await cursor.to_list(length=100)
        return [DateExceptionInDB(**d) for d in docs]

    async def upsert_exception(self, exception: DateExceptionInDB) -> DateExceptionInDB:
        """Insert or replace a date exception."""
        await self.exceptions.update_one(
            {"therapist_id": exception.therapist_id, "date": exception.date},
            {"$set": exception.model_dump()},
            upsert=True,
        )
        return exception

    async def delete_exception(self, therapist_id: str, date_str: str) -> bool:
        """Delete date exception."""
        res = await self.exceptions.delete_one({"therapist_id": therapist_id, "date": date_str})
        return res.deleted_count > 0

    async def get_extra_slots_for_range(
        self, therapist_id: str, start_date: str, end_date: str
    ) -> list[ExtraSlotInDB]:
        """Retrieve all extra slots falling within date range [start_date, end_date]."""
        cursor = self.extra_slots.find({
            "therapist_id": therapist_id,
            "date": {"$gte": start_date, "$lte": end_date},
        }).sort([("date", ASCENDING), ("start_time", ASCENDING)])
        docs = await cursor.to_list(length=200)
        return [ExtraSlotInDB(**d) for d in docs]

    async def get_extra_slot_by_id(self, slot_id: str) -> ExtraSlotInDB | None:
        """Retrieve extra slot by its ID."""
        doc = await self.extra_slots.find_one({"id": slot_id})
        return ExtraSlotInDB(**doc) if doc else None

    async def create_extra_slot(self, extra_slot: ExtraSlotInDB) -> ExtraSlotInDB:
        """Save new extra slot."""
        await self.extra_slots.insert_one(extra_slot.model_dump())
        return extra_slot

    async def delete_extra_slot(self, slot_id: str) -> bool:
        """Delete extra slot by its ID."""
        res = await self.extra_slots.delete_one({"id": slot_id})
        return res.deleted_count > 0

    async def get_unavailable_slot_ids(self, therapist_id: str) -> set[str]:
        """Fetch IDs of slots that are currently active in reservations or confirmed bookings."""
        from datetime import UTC, datetime

        now = datetime.now(UTC)
        slot_ids: set[str] = set()

        res_cursor = self.db["reservations"].find(
            {
                "therapist_id": therapist_id,
                "status": "active",
                "expires_at": {"$gt": now},
            },
            {"slot_id": 1},
        )
        res_docs = await res_cursor.to_list(length=500)
        for d in res_docs:
            if "slot_id" in d:
                slot_ids.add(d["slot_id"])

        book_cursor = self.db["bookings"].find(
            {
                "therapist_id": therapist_id,
                "status": {"$in": ["pending", "confirmed"]},
            },
            {"slot_id": 1},
        )
        book_docs = await book_cursor.to_list(length=500)
        for d in book_docs:
            if "slot_id" in d:
                slot_ids.add(d["slot_id"])

        return slot_ids

