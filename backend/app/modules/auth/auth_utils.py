"""Cryptographic, normalization, and token generation utilities."""

import hashlib
import hmac
import re
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from app.common.exceptions.app_exceptions import UnauthorizedException
from app.common.exceptions.error_codes import ErrorCode


def normalize_email(email: str | None) -> str | None:
    """Strip whitespace and lowercase email strings."""
    if not email:
        return None
    cleaned = email.strip().lower()
    return cleaned if cleaned else None


def normalize_phone(phone: str | None) -> str | None:
    """Format and standardize phone numbers to standard E.164 compatible string."""
    if not phone:
        return None
    # Strip whitespace, dashes, parentheses
    cleaned = re.sub(r"[\s\-\(\)]", "", phone.strip())

    # If it is a 10-digit Indian mobile number without country code, prefix +91
    if re.match(r"^[6-9]\d{9}$", cleaned):
        return f"+91{cleaned}"
    # If it starts with 91 and has 12 digits, prefix +
    if re.match(r"^91[6-9]\d{9}$", cleaned):
        return f"+{cleaned}"
    # If already has +, preserve
    if cleaned.startswith("+"):
        return cleaned

    return cleaned


def hash_password(password: str) -> str:
    """Hash plaintext password using bcrypt with work factor 12."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Securely verify password against bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except Exception:
        return False


def generate_secure_otp(length: int = 4) -> str:
    """Generate cryptographically secure numeric OTP of specified length."""
    digits = "0123456789"
    return "".join(secrets.choice(digits) for _ in range(length))


def hash_otp(otp: str, secret_key: str) -> str:
    """Compute HMAC-SHA256 digest of an OTP for secure storage."""
    return hmac.new(
        secret_key.encode("utf-8"),
        otp.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_otp_hash(otp: str, otp_hash: str, secret_key: str) -> bool:
    """Constant-time comparison of candidate OTP against stored HMAC hash."""
    candidate_hash = hash_otp(otp, secret_key)
    return hmac.compare_digest(candidate_hash, otp_hash)


def create_jwt_token(
    payload: dict[str, Any],
    expires_delta: timedelta,
    secret_key: str,
    algorithm: str,
) -> str:
    """Create signed JWT token with standard claims."""
    now = datetime.now(UTC)
    to_encode = payload.copy()
    to_encode.update(
        {
            "iat": now,
            "exp": now + expires_delta,
        }
    )
    return jwt.encode(to_encode, secret_key, algorithm=algorithm)


def decode_jwt_token(token: str, secret_key: str, algorithm: str) -> dict[str, Any]:
    """Decode and validate JWT signature, expiration, and payload."""
    try:
        decoded: dict[str, Any] = jwt.decode(
            token,
            secret_key,
            algorithms=[algorithm],
            options={"require": ["exp", "sub", "token_type"]},
        )
        return decoded
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedException(
            message="Token has expired",
            code=ErrorCode.AUTH_TOKEN_EXPIRED,
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise UnauthorizedException(
            message="Token is invalid or malformed",
            code=ErrorCode.AUTH_INVALID_TOKEN,
        ) from exc
