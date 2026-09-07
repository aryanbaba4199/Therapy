"""User entity factory for deterministic test data."""

import uuid
from typing import Any

from app.common.utils.datetime_utils import utc_now
from app.modules.user.user_constants import AuthProvider, UserRole, UserStatus
from app.modules.user.user_model import UserInDB


class UserFactory:
    @staticmethod
    def build(
        *,
        id: str | None = None,
        phone: str | None = None,
        email: str | None = None,
        first_name: str = "Test",
        last_name: str = "User",
        roles: list[UserRole] | None = None,
        status: UserStatus = UserStatus.ACTIVE,
        is_verified: bool = True,
        auth_providers: list[AuthProvider] | None = None,
        password_hash: str | None = "$2b$12$e8xH2g8YqgZf8e1Z.u6vUu1e1V1e1V1e1V1e1V1e1V1e1V1e1V1e",
        profile: dict[str, Any] | None = None,
        preferences: dict[str, Any] | None = None,
    ) -> UserInDB:
        user_id = id or str(uuid.uuid4())
        user_phone = phone or f"+9198{uuid.uuid4().hex[:8]}"
        user_email = email or f"user_{user_id[:8]}@example.com"
        now = utc_now()

        return UserInDB(
            id=user_id,
            phone=user_phone,
            email=user_email,
            first_name=first_name,
            last_name=last_name,
            roles=roles or [UserRole.USER],
            status=status,
            is_verified=is_verified,
            auth_providers=auth_providers or [AuthProvider.PASSWORD],
            password_hash=password_hash,
            profile=profile or {},
            preferences=preferences or {"language": "en", "notifications": True},
            created_at=now,
            updated_at=now,
            last_login_at=now,
        )

    @staticmethod
    async def create(mock_db: Any, **kwargs: Any) -> UserInDB:
        user = UserFactory.build(**kwargs)
        await mock_db["users"].insert_one(user.model_dump(mode="json"))
        return user
