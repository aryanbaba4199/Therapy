"""Pydantic schemas for User API requests and responses."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.user.user_constants import AuthProvider, UserRole, UserStatus
from app.modules.user.user_model import UserInDB


class UserProfileResponse(BaseModel):
    """Public, sanitized representation of a user profile (no password hash)."""

    id: str
    first_name: str
    last_name: str
    email: str | None = None
    phone: str | None = None
    roles: list[UserRole]
    status: UserStatus
    is_verified: bool
    auth_providers: list[AuthProvider]
    profile: dict[str, Any]
    preferences: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None = None

    @classmethod
    def from_user_db(cls, user: UserInDB) -> "UserProfileResponse":
        """Convert database entity to safe public response schema."""
        return cls(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            phone=user.phone,
            roles=user.roles,
            status=user.status,
            is_verified=user.is_verified,
            auth_providers=user.auth_providers,
            profile=user.profile,
            preferences=user.preferences,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login_at=user.last_login_at,
        )


class UserUpdateProfileRequest(BaseModel):
    """Self-service profile update request payload."""

    first_name: str | None = Field(default=None, min_length=1, max_length=50)
    last_name: str | None = Field(default=None, min_length=1, max_length=50)
    profile: dict[str, Any] | None = None
    preferences: dict[str, Any] | None = None
