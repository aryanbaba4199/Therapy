"""MongoDB repository for Packages and User Entitlements."""

from datetime import UTC, datetime
from typing import Any

from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo import ASCENDING, IndexModel

from app.modules.package.package_constants import PackageStatus
from app.modules.package.package_model import PackageProductInDB, UserPackageInDB


class PackageRepository:
    """Repository accessing `package_products` and `user_packages` collections."""

    def __init__(self, db: AsyncIOMotorDatabase[dict[str, Any]]) -> None:
        self.db = db
        self.products: AsyncIOMotorCollection[dict[str, Any]] = db["package_products"]
        self.user_packages: AsyncIOMotorCollection[dict[str, Any]] = db["user_packages"]

    async def ensure_indexes(self) -> None:
        """Initialize database indexes."""
        await self.products.create_indexes([
            IndexModel([("id", ASCENDING)], unique=True, name="idx_package_product_id"),
            IndexModel([("is_active", ASCENDING)], name="idx_package_product_active"),
        ])
        await self.user_packages.create_indexes([
            IndexModel([("id", ASCENDING)], unique=True, name="idx_user_package_id"),
            IndexModel(
                [("user_id", ASCENDING), ("status", ASCENDING), ("expires_at", ASCENDING)],
                name="idx_user_package_user_status",
            ),
            IndexModel(
                [("payment_id", ASCENDING)],
                unique=True,
                sparse=True,
                name="idx_user_packages_payment_id_unique",
            ),
        ])

    async def create_product(self, product: PackageProductInDB) -> PackageProductInDB:
        await self.products.insert_one(product.model_dump())
        return product

    async def get_product_by_id(self, product_id: str) -> PackageProductInDB | None:
        doc = await self.products.find_one({"id": product_id})
        return PackageProductInDB(**doc) if doc else None

    async def list_active_products(self) -> list[PackageProductInDB]:
        cursor = self.products.find({"is_active": True}).sort("price_minor", ASCENDING)
        docs = await cursor.to_list(length=100)
        return [PackageProductInDB(**d) for d in docs]

    async def create_user_package(self, user_pkg: UserPackageInDB) -> UserPackageInDB:
        await self.user_packages.insert_one(user_pkg.model_dump())
        return user_pkg

    async def get_user_package_by_id(self, user_pkg_id: str) -> UserPackageInDB | None:
        doc = await self.user_packages.find_one({"id": user_pkg_id})
        return UserPackageInDB(**doc) if doc else None

    async def get_user_package_by_payment_id(self, payment_id: str) -> UserPackageInDB | None:
        """Find user package entitlement associated with a specific payment ID."""
        doc = await self.user_packages.find_one({"payment_id": payment_id})
        return UserPackageInDB(**doc) if doc else None

    async def list_user_packages(self, user_id: str) -> list[UserPackageInDB]:
        cursor = self.user_packages.find({"user_id": user_id}).sort("created_at", -1)
        docs = await cursor.to_list(length=100)
        return [UserPackageInDB(**d) for d in docs]

    async def get_active_usable_packages(self, user_id: str) -> list[UserPackageInDB]:
        now = datetime.now(UTC)
        cursor = self.user_packages.find({
            "user_id": user_id,
            "status": PackageStatus.ACTIVE.value,
            "remaining_sessions": {"$gt": 0},
            "expires_at": {"$gte": now},
        }).sort("expires_at", ASCENDING)
        docs = await cursor.to_list(length=100)
        return [UserPackageInDB(**d) for d in docs]

    async def consume_session_atomic(self, user_pkg_id: str, user_id: str) -> bool:
        """Atomically decrement remaining_sessions if > 0 and unexpired."""
        now = datetime.now(UTC)
        query = {
            "id": user_pkg_id,
            "user_id": user_id,
            "status": PackageStatus.ACTIVE.value,
            "remaining_sessions": {"$gt": 0},
            "expires_at": {"$gte": now},
        }
        update = {"$inc": {"remaining_sessions": -1}, "$set": {"updated_at": now}}

        res = await self.user_packages.find_one_and_update(
            query, update, return_document=True
        )
        if not res:
            return False

        # If remaining_sessions hit 0, mark EXHAUSTED
        if res.get("remaining_sessions", 0) <= 0:
            await self.user_packages.update_one(
                {"id": user_pkg_id},
                {"$set": {"status": PackageStatus.EXHAUSTED.value}},
            )
        return True
