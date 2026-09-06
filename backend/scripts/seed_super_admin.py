"""Seed script to inject or update the Super Admin user in MongoDB."""

import asyncio
import uuid
from motor.motor_asyncio import AsyncIOMotorClient

from app.common.utils.datetime_utils import utc_now
from app.core.config import get_settings
from app.modules.auth.auth_utils import hash_password
from app.modules.user.user_constants import AuthProvider, UserRole, UserStatus
from app.modules.user.user_model import UserInDB


async def seed_super_admin() -> None:
    settings = get_settings()
    client = AsyncIOMotorClient(
        settings.mongodb_uri,
        serverSelectionTimeoutMS=settings.mongodb_timeout_ms,
    )
    db = client[settings.mongodb_database]

    email = "aryanbaba4199@gmail.com"
    plain_password = "Aryan@7277"
    hashed_pw = hash_password(plain_password)

    users_col = db["users"]
    existing_user = await users_col.find_one({"email": email})

    now = utc_now()
    roles = [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.USER]

    if existing_user:
        await users_col.update_one(
            {"_id": existing_user["_id"]},
            {
                "$set": {
                    "password_hash": hashed_pw,
                    "roles": [r.value for r in roles],
                    "status": UserStatus.ACTIVE.value,
                    "is_verified": True,
                    "updated_at": now,
                },
                "$addToSet": {
                    "auth_providers": AuthProvider.PASSWORD.value,
                },
            },
        )
        print(f"Super Admin user '{email}' updated successfully (ID: {existing_user.get('id')}).")
    else:
        new_user = UserInDB(
            id=str(uuid.uuid4()),
            first_name="Aryan",
            last_name="SuperAdmin",
            email=email,
            password_hash=hashed_pw,
            roles=roles,
            status=UserStatus.ACTIVE,
            is_verified=True,
            auth_providers=[AuthProvider.PASSWORD],
            profile={"bio": "Platform Project Owner & Super Administrator"},
            created_at=now,
            updated_at=now,
        )
        await users_col.insert_one(new_user.model_dump())
        print(f"Super Admin user '{email}' created successfully (ID: {new_user.id}).")

    client.close()


if __name__ == "__main__":
    asyncio.run(seed_super_admin())
