"""Database access repository for User collection in MongoDB."""

from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, IndexModel

from app.common.utils.datetime_utils import utc_now
from app.modules.user.user_model import UserInDB


class UserRepository:
    """Encapsulates MongoDB interactions for the User entity."""

    COLLECTION_NAME = "users"

    def __init__(self, db: AsyncIOMotorDatabase[dict[str, Any]]) -> None:
        self.collection = db[self.COLLECTION_NAME]

    async def ensure_indexes(self) -> None:
        """Create unique and query indexes on the users collection."""
        indexes = [
            IndexModel([("email", ASCENDING)], unique=True, sparse=True, name="idx_user_email"),
            IndexModel([("phone", ASCENDING)], unique=True, sparse=True, name="idx_user_phone"),
            IndexModel([("status", ASCENDING)], name="idx_user_status"),
            IndexModel([("roles", ASCENDING)], name="idx_user_roles"),
        ]
        await self.collection.create_indexes(indexes)

    async def get_by_id(self, user_id: str) -> UserInDB | None:
        """Retrieve user by their unique identifier."""
        doc = await self.collection.find_one({"id": user_id})
        return UserInDB(**doc) if doc else None

    async def get_by_email(self, email: str) -> UserInDB | None:
        """Retrieve user by normalized email."""
        doc = await self.collection.find_one({"email": email})
        return UserInDB(**doc) if doc else None

    async def get_by_phone(self, phone: str) -> UserInDB | None:
        """Retrieve user by normalized phone."""
        doc = await self.collection.find_one({"phone": phone})
        return UserInDB(**doc) if doc else None

    async def create(self, user: UserInDB) -> UserInDB:
        """Insert new user document."""
        data = user.model_dump()
        await self.collection.insert_one(data)
        return user

    async def update(self, user_id: str, updates: dict[str, Any]) -> UserInDB | None:
        """Update specific fields of an existing user."""
        updates["updated_at"] = utc_now()
        await self.collection.update_one({"id": user_id}, {"$set": updates})
        return await self.get_by_id(user_id)
