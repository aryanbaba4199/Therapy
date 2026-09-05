"""Request and response schemas for authentication workflows."""

from pydantic import BaseModel, Field, field_validator, model_validator

from app.modules.auth.auth_constants import OtpChannel
from app.modules.auth.auth_utils import normalize_email, normalize_phone
from app.modules.user.user_schema import UserProfileResponse


class RegisterRequest(BaseModel):
    """User registration payload."""

    first_name: str = Field(min_length=1, max_length=50, description="User's first name")
    last_name: str = Field(min_length=1, max_length=50, description="User's last name")
    email: str | None = Field(default=None, description="User's email address")
    phone: str | None = Field(default=None, description="User's phone number")
    password: str = Field(min_length=8, max_length=128, description="User's password")
    language: str = Field(
        default="en", description="Preferred interface language ('en', 'ml', 'ta')"
    )

    @field_validator("email", mode="after")
    @classmethod
    def clean_email(cls, v: str | None) -> str | None:
        return normalize_email(v)

    @field_validator("phone", mode="after")
    @classmethod
    def clean_phone(cls, v: str | None) -> str | None:
        return normalize_phone(v)

    @model_validator(mode="after")
    def validate_contact(self) -> "RegisterRequest":
        if not self.email and not self.phone:
            raise ValueError("Either email or phone must be provided for registration")
        return self


class LoginRequest(BaseModel):
    """Email or Phone + Password authentication request."""

    identifier: str = Field(min_length=3, description="Email or phone number")
    password: str = Field(min_length=1, description="Account password")


class SendOtpRequest(BaseModel):
    """OTP dispatch request."""

    phone: str = Field(min_length=7, description="Phone number to receive OTP")
    channel: OtpChannel = Field(default=OtpChannel.WHATSAPP, description="OTP delivery channel")

    @field_validator("phone", mode="after")
    @classmethod
    def clean_phone(cls, v: str) -> str:
        cleaned = normalize_phone(v)
        if not cleaned:
            raise ValueError("A valid phone number must be provided")
        return cleaned


class SendOtpResponse(BaseModel):
    """Metadata returned after OTP dispatch."""

    phone: str
    channel: OtpChannel
    cooldown_seconds: int
    expires_in: int


class VerifyOtpRequest(BaseModel):
    """OTP verification request."""

    phone: str = Field(min_length=7, description="Phone number being verified")
    otp: str = Field(min_length=4, max_length=6, description="Received numeric OTP code")

    @field_validator("phone", mode="after")
    @classmethod
    def clean_phone(cls, v: str) -> str:
        cleaned = normalize_phone(v)
        if not cleaned:
            raise ValueError("A valid phone number must be provided")
        return cleaned


class RefreshTokenRequest(BaseModel):
    """Manual refresh token request (used when not relying exclusively on cookies)."""

    refresh_token: str | None = None


class TokenResponse(BaseModel):
    """Standard authentication response containing token and user profile."""

    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int
    user: UserProfileResponse
