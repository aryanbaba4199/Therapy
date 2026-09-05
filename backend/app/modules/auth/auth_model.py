from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.common.utils.datetime_utils import ensure_utc, utc_now
from app.modules.auth.auth_constants import OtpChannel, OtpStatus


class OtpDocument(BaseModel):
    """Stores hashed OTP record with rate limiting and verification status."""

    id: str = Field(description="Unique OTP request UUID")
    phone: str = Field(description="Normalized E.164 phone number")
    otp_hash: str = Field(description="HMAC-SHA256 digest of plaintext OTP")
    channel: OtpChannel = Field(default=OtpChannel.WHATSAPP)
    status: OtpStatus = Field(default=OtpStatus.PENDING)
    attempts: int = Field(default=0, description="Failed verification attempts count")
    cooldown_until: datetime = Field(description="Timestamp until next OTP can be requested")
    expires_at: datetime = Field(description="Timestamp when OTP becomes invalid")
    created_at: datetime = Field(default_factory=utc_now)
    verified_at: datetime | None = None

    @field_validator("cooldown_until", "expires_at", "created_at", "verified_at", mode="after")
    @classmethod
    def make_tz_aware(cls, v: datetime | None) -> datetime | None:
        return ensure_utc(v) if v is not None else None


class RefreshSessionDocument(BaseModel):
    """Tracks active refresh token sessions for revocation and rotation."""

    id: str = Field(description="Unique JWT JTI string identifier")
    user_id: str = Field(description="User ID associated with this session")
    token_hash: str = Field(description="SHA-256 hash of refresh token string")
    is_revoked: bool = Field(default=False)
    user_agent: str | None = None
    ip_address: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime = Field(description="Session expiration timestamp")
    revoked_at: datetime | None = None

    @field_validator("created_at", "expires_at", "revoked_at", mode="after")
    @classmethod
    def make_tz_aware(cls, v: datetime | None) -> datetime | None:
        return ensure_utc(v) if v is not None else None
