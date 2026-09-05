"""MongoDB repository persistence layer for Reviews."""

from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.utils.datetime_utils import utc_now
from app.modules.review.review_constants import ReviewStatus
from app.modules.review.review_model import ReviewInDB
from app.modules.review.review_schema import TherapistRatingSummaryResponse


class ReviewRepository:
    """Repository managing MongoDB operations for `reviews` collection."""

    def __init__(self, db: AsyncIOMotorDatabase[dict[str, Any]]) -> None:
        self.collection = db.get_collection("reviews")

    async def create_indexes(self) -> None:
        """Create database indexes for uniqueness, security, and lookup performance."""
        indexes = [
            # Strictly enforces 1-to-1 invariant: exactly one review per completed session
            IndexModel(
                [("session_id", ASCENDING)],
                unique=True,
                name="idx_reviews_session_id_unique",
            ),
            # Public therapist review listing and aggregation
            IndexModel(
                [
                    ("therapist_id", ASCENDING),
                    ("status", ASCENDING),
                    ("created_at", DESCENDING),
                ],
                name="idx_reviews_therapist_status_created",
            ),
            # Client review history
            IndexModel(
                [("client_id", ASCENDING), ("created_at", DESCENDING)],
                name="idx_reviews_client_created",
            ),
        ]
        await self.collection.create_indexes(indexes)

    async def create(self, review: ReviewInDB) -> ReviewInDB:
        """Insert a new review document into the database."""
        doc = review.model_dump()
        await self.collection.insert_one(doc)
        return review

    async def get_by_id(self, review_id: str) -> ReviewInDB | None:
        """Retrieve a review by unique UUID."""
        doc = await self.collection.find_one({"id": review_id})
        if not doc:
            return None
        return ReviewInDB.model_validate(doc)

    async def get_by_session_id(self, session_id: str) -> ReviewInDB | None:
        """Retrieve an existing review for a specific session."""
        doc = await self.collection.find_one({"session_id": session_id})
        if not doc:
            return None
        return ReviewInDB.model_validate(doc)

    async def list_for_therapist(
        self,
        therapist_id: str,
        status: ReviewStatus = ReviewStatus.PUBLISHED,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[ReviewInDB], int]:
        """List reviews for a therapist with pagination."""
        filter_query: dict[str, Any] = {
            "therapist_id": therapist_id,
            "status": status.value,
        }
        total = await self.collection.count_documents(filter_query)
        skip = (page - 1) * limit

        cursor = (
            self.collection.find(filter_query)
            .sort("created_at", DESCENDING)
            .skip(skip)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        return [ReviewInDB.model_validate(d) for d in docs], total

    async def list_for_client(
        self,
        client_id: str,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[ReviewInDB], int]:
        """List reviews authored by a client with pagination."""
        filter_query: dict[str, Any] = {"client_id": client_id}
        total = await self.collection.count_documents(filter_query)
        skip = (page - 1) * limit

        cursor = (
            self.collection.find(filter_query)
            .sort("created_at", DESCENDING)
            .skip(skip)
            .limit(limit)
        )
        docs = await cursor.to_list(length=limit)
        return [ReviewInDB.model_validate(d) for d in docs], total

    async def get_therapist_rating_summary(
        self, therapist_id: str
    ) -> TherapistRatingSummaryResponse:
        """Compute aggregated average rating and star distribution using MongoDB pipeline."""
        pipeline: list[dict[str, Any]] = [
            {
                "$match": {
                    "therapist_id": therapist_id,
                    "status": ReviewStatus.PUBLISHED.value,
                }
            },
            {
                "$facet": {
                    "overall": [
                        {
                            "$group": {
                                "_id": None,
                                "avg_rating": {"$avg": "$rating"},
                                "total_count": {"$sum": 1},
                            }
                        }
                    ],
                    "distribution": [
                        {
                            "$group": {
                                "_id": "$rating",
                                "count": {"$sum": 1},
                            }
                        }
                    ],
                }
            },
        ]
        cursor = self.collection.aggregate(pipeline)
        result = await cursor.to_list(length=1)

        distribution: dict[str, int] = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
        avg_rating = 0.0
        total_count = 0

        if result:
            facet_data = result[0]
            overall = facet_data.get("overall", [])
            if overall:
                avg_rating = round(float(overall[0].get("avg_rating", 0.0)), 2)
                total_count = int(overall[0].get("total_count", 0))

            dist_list = facet_data.get("distribution", [])
            for item in dist_list:
                rating_key = str(item.get("_id", ""))
                if rating_key in distribution:
                    distribution[rating_key] = int(item.get("count", 0))

        return TherapistRatingSummaryResponse(
            therapist_id=therapist_id,
            average_rating=avg_rating,
            review_count=total_count,
            distribution=distribution,
        )

    async def update_status(
        self, review_id: str, status: ReviewStatus
    ) -> ReviewInDB | None:
        """Update review publication/moderation status."""
        doc = await self.collection.find_one_and_update(
            {"id": review_id},
            {"$set": {"status": status.value, "updated_at": utc_now()}},
            return_document=True,
        )
        if not doc:
            return None
        return ReviewInDB.model_validate(doc)
