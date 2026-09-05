"""Asynchronous MongoDB connection management using Motor."""

import logging
from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure

from app.core.config import get_settings

logger = logging.getLogger("app.database")


class MongoManager:
    """Lifecycle-safe MongoDB connection manager."""

    def __init__(self) -> None:
        self.client: AsyncIOMotorClient[dict[str, Any]] | None = None
        self.db: AsyncIOMotorDatabase[dict[str, Any]] | None = None

    async def connect(self) -> None:
        """Initialize MongoDB client and verify connectivity with a ping."""
        if self.client is not None:
            logger.info("MongoDB client already initialized.")
            return

        settings = get_settings()
        logger.info("Connecting to MongoDB at %s...", settings.mongodb_uri)

        try:
            self.client = AsyncIOMotorClient(
                settings.mongodb_uri,
                minPoolSize=settings.mongodb_min_pool_size,
                maxPoolSize=settings.mongodb_max_pool_size,
                serverSelectionTimeoutMS=settings.mongodb_timeout_ms,
            )
            self.db = self.client[settings.mongodb_database]

            # Verify connection via admin ping
            await self.client.admin.command("ping")
            logger.info("Successfully connected to MongoDB database: %s", settings.mongodb_database)
        except (ConnectionFailure, Exception) as exc:
            logger.warning(
                "MongoDB ping failed on startup (%s). Service starting in disconnected mode.", exc
            )

    async def disconnect(self) -> None:
        """Close MongoDB client connection pool cleanly."""
        if self.client is not None:
            logger.info("Closing MongoDB connection pool...")
            self.client.close()
            self.client = None
            self.db = None
            logger.info("MongoDB connection closed.")

    async def ping(self) -> bool:
        """Check live database responsiveness."""
        if self.client is None:
            return False
        try:
            await self.client.admin.command("ping")
            return True
        except Exception:
            return False

    def get_database(self) -> AsyncIOMotorDatabase[dict[str, Any]]:
        """Retrieve the active database instance, raising an error if uninitialized."""
        if self.db is None:
            raise RuntimeError(
                "Database connection has not been initialized. Ensure connect() was called."
            )
        return self.db


mongo_manager = MongoManager()


async def get_database() -> AsyncIOMotorDatabase[dict[str, Any]]:
    """FastAPI dependency for injecting the active MongoDB database instance."""
    return mongo_manager.get_database()
