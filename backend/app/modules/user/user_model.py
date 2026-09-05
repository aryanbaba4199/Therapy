from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.common.utils.datetime_utils import ensure_utc, utc_now
from app.modules.user.user_constants import AuthProvider, UserRole, UserStatus


class UserInDB(BaseModel):
    """User representation stored in MongoDB collection `users`."""

    id: str = Field(description="Unique string identifier (UUID)")
    first_name: str
    last_name: str
    email: str | None = None
    phone: str | None = None
    password_hash: str | None = None
    roles: list[UserRole] = Field(default_factory=lambda: [UserRole.USER])
    status: UserStatus = Field(default=UserStatus.ACTIVE)
    is_verified: bool = False
    auth_providers: list[AuthProvider] = Field(default_factory=list)
    profile: dict[str, Any] = Field(default_factory=dict)
    preferences: dict[str, Any] = Field(
        default_factory=lambda: {"language": "en", "notifications": True}
    )
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    last_login_at: datetime | None = None

    @field_validator("created_at", "updated_at", "last_login_at", mode="after")
    @classmethod
    def make_tz_aware(cls, v: datetime | None) -> datetime | None:
        return ensure_utc(v) if v is not None else None
