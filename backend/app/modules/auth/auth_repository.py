"""Database repository for OTP records and Refresh Sessions in MongoDB."""

from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, IndexModel

from app.common.utils.datetime_utils import utc_now
from app.modules.auth.auth_constants import OtpStatus
from app.modules.auth.auth_model import OtpDocument, RefreshSessionDocument


class AuthRepository:
    """Encapsulates MongoDB operations for authentication collections."""

    OTP_COLLECTION = "auth_otps"
    REFRESH_COLLECTION = "auth_refresh_sessions"

    def __init__(self, db: AsyncIOMotorDatabase[dict[str, Any]]) -> None:
        self.otp_coll = db[self.OTP_COLLECTION]
        self.refresh_coll = db[self.REFRESH_COLLECTION]

    async def ensure_indexes(self) -> None:
        """Create indexes for performance and security lookups."""
        otp_indexes = [
            IndexModel(
                [("phone", ASCENDING), ("created_at", DESCENDING)], name="idx_otp_phone_created"
            ),
            IndexModel([("expires_at", ASCENDING)], expireAfterSeconds=0, name="idx_otp_ttl"),
        ]
        await self.otp_coll.create_indexes(otp_indexes)

        refresh_indexes = [
            IndexModel([("id", ASCENDING)], unique=True, name="idx_refresh_jti"),
            IndexModel([("user_id", ASCENDING)], name="idx_refresh_user_id"),
            IndexModel([("expires_at", ASCENDING)], expireAfterSeconds=0, name="idx_refresh_ttl"),
        ]
        await self.refresh_coll.create_indexes(refresh_indexes)

    async def create_otp(self, doc: OtpDocument) -> OtpDocument:
        """Insert a newly issued OTP record."""
        data = doc.model_dump()
        await self.otp_coll.insert_one(data)
        return doc

    async def get_latest_otp(self, phone: str) -> OtpDocument | None:
        """Retrieve the most recent OTP record issued for a phone number."""
        doc = await self.otp_coll.find_one(
            {"phone": phone},
            sort=[("created_at", DESCENDING)],
        )
        return OtpDocument(**doc) if doc else None

    async def increment_otp_attempts(self, otp_id: str) -> int:
        """Increment failed attempts counter and return the updated count."""
        result = await self.otp_coll.find_one_and_update(
            {"id": otp_id},
            {"$inc": {"attempts": 1}},
            return_document=True,
        )
        if result and "attempts" in result:
            return int(result["attempts"])
        return 1

    async def mark_otp_verified(self, otp_id: str) -> None:
        """Mark OTP status as verified upon successful authentication."""
        await self.otp_coll.update_one(
            {"id": otp_id},
            {
                "$set": {
                    "status": OtpStatus.VERIFIED,
                    "verified_at": utc_now(),
                }
            },
        )

    async def create_refresh_session(self, doc: RefreshSessionDocument) -> RefreshSessionDocument:
        """Record a newly minted refresh session."""
        data = doc.model_dump()
        await self.refresh_coll.insert_one(data)
        return doc

    async def get_refresh_session(self, jti: str) -> RefreshSessionDocument | None:
        """Retrieve refresh session by unique JTI."""
        doc = await self.refresh_coll.find_one({"id": jti})
        return RefreshSessionDocument(**doc) if doc else None

    async def revoke_refresh_session(self, jti: str) -> None:
        """Revoke a refresh session by JTI (e.g. on rotation or single logout)."""
        await self.refresh_coll.update_one(
            {"id": jti},
            {
                "$set": {
                    "is_revoked": True,
                    "revoked_at": utc_now(),
                }
            },
        )

    async def revoke_all_user_refresh_sessions(self, user_id: str) -> None:
        """Revoke all active sessions for a user (e.g. password change or global logout)."""
        await self.refresh_coll.update_many(
            {"user_id": user_id, "is_revoked": False},
            {
                "$set": {
                    "is_revoked": True,
                    "revoked_at": utc_now(),
                }
            },
        )
