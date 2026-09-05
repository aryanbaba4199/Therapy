"""Database repository for Therapist entities in MongoDB."""

from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, TEXT, IndexModel

from app.common.utils.datetime_utils import utc_now
from app.modules.therapist.therapist_constants import TherapistSortBy
from app.modules.therapist.therapist_model import TherapistInDB


class TherapistRepository:
    """Encapsulates MongoDB operations for the therapists collection."""

    COLLECTION_NAME = "therapists"

    def __init__(self, db: AsyncIOMotorDatabase[dict[str, Any]]) -> None:
        self.collection = db[self.COLLECTION_NAME]

    async def ensure_indexes(self) -> None:
        """Create query, uniqueness, and search indexes."""
        indexes = [
            IndexModel(
                [("user_id", ASCENDING)], unique=True, sparse=True, name="idx_therapist_user_id"
            ),
            IndexModel(
                [("status", ASCENDING), ("verification.status", ASCENDING)],
                name="idx_therapist_status_verification",
            ),
            IndexModel([("specialization", ASCENDING)], name="idx_therapist_specialization"),
            IndexModel([("languages", ASCENDING)], name="idx_therapist_languages"),
            IndexModel([("session_modes", ASCENDING)], name="idx_therapist_session_modes"),
            IndexModel([("expertises", ASCENDING)], name="idx_therapist_expertises"),
            IndexModel([("experience_years", DESCENDING)], name="idx_therapist_experience"),
            IndexModel([("pricing.amount", ASCENDING)], name="idx_therapist_price"),
            IndexModel([("therapy_hours", DESCENDING)], name="idx_therapist_hours"),
            IndexModel(
                [
                    ("display_name", TEXT),
                    ("first_name", TEXT),
                    ("last_name", TEXT),
                    ("designation", TEXT),
                ],
                name="idx_therapist_text_search",
            ),
        ]
        await self.collection.create_indexes(indexes)

    async def get_by_id(self, therapist_id: str) -> TherapistInDB | None:
        """Retrieve therapist by ID."""
        doc = await self.collection.find_one({"id": therapist_id})
        return TherapistInDB(**doc) if doc else None

    async def get_by_user_id(self, user_id: str) -> TherapistInDB | None:
        """Retrieve therapist by user ID."""
        doc = await self.collection.find_one({"user_id": user_id})
        return TherapistInDB(**doc) if doc else None

    async def create(self, therapist: TherapistInDB) -> TherapistInDB:
        """Insert a new therapist document."""
        data = therapist.model_dump()
        await self.collection.insert_one(data)
        return therapist

    async def update(self, therapist_id: str, updates: dict[str, Any]) -> TherapistInDB | None:
        """Update fields of an existing therapist."""
        updates["updated_at"] = utc_now()
        await self.collection.update_one({"id": therapist_id}, {"$set": updates})
        return await self.get_by_id(therapist_id)

    async def find_paginated(
        self,
        filter_query: dict[str, Any],
        sort_by: TherapistSortBy,
        skip: int,
        limit: int,
    ) -> tuple[list[TherapistInDB], int]:
        """Execute paginated discovery query with whitelisted sorting."""
        total_count = await self.collection.count_documents(filter_query)

        sort_criteria: list[tuple[str, int]]
        if sort_by == TherapistSortBy.EXPERIENCE_DESC:
            sort_criteria = [("experience_years", DESCENDING), ("created_at", DESCENDING)]
        elif sort_by == TherapistSortBy.PRICE_ASC:
            sort_criteria = [("pricing.amount", ASCENDING), ("created_at", DESCENDING)]
        elif sort_by == TherapistSortBy.PRICE_DESC:
            sort_criteria = [("pricing.amount", DESCENDING), ("created_at", DESCENDING)]
        elif sort_by == TherapistSortBy.THERAPY_HOURS_DESC:
            sort_criteria = [("therapy_hours", DESCENDING), ("created_at", DESCENDING)]
        else:
            # Default: RELEVANCE
            sort_criteria = [
                ("experience_years", DESCENDING),
                ("therapy_hours", DESCENDING),
                ("created_at", DESCENDING),
            ]

        cursor = self.collection.find(filter_query).sort(sort_criteria).skip(skip).limit(limit)
        docs = await cursor.to_list(length=limit)
        items = [TherapistInDB(**doc) for doc in docs]
        return items, total_count
