"""Centralized application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly typed application configuration sourced from environment variables."""

    # Application metadata
    app_name: str = Field(default="Oppam Counselling Platform API", alias="APP_NAME")
    app_env: Literal["development", "test", "staging", "production"] = Field(
        default="development", alias="APP_ENV"
    )
    debug: bool = Field(default=False, alias="DEBUG")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")
    app_version: str = Field(default="1.0.0", alias="APP_VERSION")

    # Server configuration
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    # MongoDB connection
    mongodb_uri: str = Field(default="mongodb://localhost:27017", alias="MONGODB_URI")
    mongodb_database: str = Field(default="oppam_therapy", alias="MONGODB_DATABASE")
    mongodb_min_pool_size: int = Field(default=10, alias="MONGODB_MIN_POOL_SIZE")
    mongodb_max_pool_size: int = Field(default=50, alias="MONGODB_MAX_POOL_SIZE")
    mongodb_timeout_ms: int = Field(default=5000, alias="MONGODB_TIMEOUT_MS")

    # CORS settings
    cors_origins: list[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"],
        alias="CORS_ORIGINS",
    )
    cors_allow_credentials: bool = Field(default=True, alias="CORS_ALLOW_CREDENTIALS")

    # Security & JWT settings
    jwt_secret_key: str = Field(
        default="replace-this-in-production-with-a-secure-secret-key-min-32-chars",
        alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=60, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    jwt_refresh_token_expire_days: int = Field(default=7, alias="JWT_REFRESH_TOKEN_EXPIRE_DAYS")

    # OTP settings
    otp_length: int = Field(default=4, alias="OTP_LENGTH")
    otp_expire_seconds: int = Field(default=300, alias="OTP_EXPIRE_SECONDS")
    otp_resend_cooldown_seconds: int = Field(default=30, alias="OTP_RESEND_COOLDOWN_SECONDS")
    otp_max_attempts: int = Field(default=5, alias="OTP_MAX_ATTEMPTS")
    otp_provider: Literal["mock", "sms", "whatsapp"] = Field(default="mock", alias="OTP_PROVIDER")

    # Cookie settings for Refresh Token
    refresh_cookie_name: str = Field(default="oppam_refresh_token", alias="REFRESH_COOKIE_NAME")
    refresh_cookie_secure: bool = Field(default=False, alias="REFRESH_COOKIE_SECURE")
    refresh_cookie_samesite: Literal["lax", "strict", "none"] = Field(
        default="lax", alias="REFRESH_COOKIE_SAMESITE"
    )
    refresh_cookie_httponly: bool = Field(default=True, alias="REFRESH_COOKIE_HTTPONLY")
    refresh_cookie_domain: str | None = Field(default=None, alias="REFRESH_COOKIE_DOMAIN")
    refresh_cookie_path: str = Field(default="/api/v1/auth", alias="REFRESH_COOKIE_PATH")

    # Logging settings
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_json_format: bool = Field(default=False, alias="LOG_JSON_FORMAT")

    # Request ID header name
    request_id_header: str = Field(default="X-Request-ID", alias="REQUEST_ID_HEADER")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached singleton application settings instance."""
    return Settings()
