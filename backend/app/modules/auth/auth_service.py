"""Domain business logic for authentication, OTP verification, and session lifecycle."""

import logging
import uuid
from abc import ABC, abstractmethod
from datetime import timedelta
from typing import Any

from app.common.exceptions.app_exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    RateLimitedException,
    UnauthorizedException,
)
from app.common.exceptions.error_codes import ErrorCode
from app.common.utils.datetime_utils import utc_now
from app.core.config import Settings
from app.modules.auth.auth_constants import OtpChannel, OtpStatus, TokenType
from app.modules.auth.auth_model import OtpDocument, RefreshSessionDocument
from app.modules.auth.auth_repository import AuthRepository
from app.modules.auth.auth_schema import (
    LoginRequest,
    RegisterRequest,
    SendOtpRequest,
    SendOtpResponse,
    TokenResponse,
    VerifyOtpRequest,
)
from app.modules.auth.auth_utils import (
    create_jwt_token,
    decode_jwt_token,
    generate_secure_otp,
    hash_otp,
    hash_password,
    normalize_email,
    normalize_phone,
    verify_otp_hash,
    verify_password,
)
from app.modules.user.user_constants import AuthProvider, UserRole, UserStatus
from app.modules.user.user_model import UserInDB
from app.modules.user.user_repository import UserRepository
from app.modules.user.user_schema import UserProfileResponse

logger = logging.getLogger(__name__)


class OtpProvider(ABC):
    """Abstract interface for OTP delivery services."""

    @abstractmethod
    async def send_otp(self, phone: str, code: str, channel: OtpChannel) -> bool:
        """Transmit OTP code through designated channel."""
        pass


class MockOtpProvider(OtpProvider):
    """Development and test provider logging OTP to console or mock memory."""

    async def send_otp(self, phone: str, code: str, channel: OtpChannel) -> bool:
        logger.info(f"[DEV MOCK OTP] Channel: {channel.value} | Phone: {phone} | Code: {code}")
        return True


class AuthService:
    """Core domain service for user authentication and authorization."""

    def __init__(
        self,
        user_repo: UserRepository,
        auth_repo: AuthRepository,
        settings: Settings,
        otp_provider: OtpProvider | None = None,
    ) -> None:
        self.user_repo = user_repo
        self.auth_repo = auth_repo
        self.settings = settings
        self.otp_provider = otp_provider or MockOtpProvider()

    async def register(
        self,
        req: RegisterRequest,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> TokenResponse:
        """Register a new user via email/phone and password."""
        if req.email:
            existing_email = await self.user_repo.get_by_email(req.email)
            if existing_email:
                raise ConflictException(
                    message="A user with this email address already exists",
                    code=ErrorCode.USER_EMAIL_ALREADY_EXISTS,
                )

        if req.phone:
            existing_phone = await self.user_repo.get_by_phone(req.phone)
            if existing_phone:
                raise ConflictException(
                    message="A user with this phone number already exists",
                    code=ErrorCode.USER_PHONE_ALREADY_EXISTS,
                )

        pw_hash = hash_password(req.password)
        user_id = str(uuid.uuid4())
        now = utc_now()

        user = UserInDB(
            id=user_id,
            first_name=req.first_name,
            last_name=req.last_name,
            email=req.email,
            phone=req.phone,
            password_hash=pw_hash,
            roles=[UserRole.USER],
            status=UserStatus.ACTIVE,
            is_verified=False,
            auth_providers=[AuthProvider.PASSWORD],
            preferences={"language": req.language, "notifications": True},
            created_at=now,
            updated_at=now,
            last_login_at=now,
        )
        await self.user_repo.create(user)

        return await self._issue_tokens(user, user_agent=user_agent, ip_address=ip_address)

    async def login(
        self,
        req: LoginRequest,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> TokenResponse:
        """Authenticate user using identifier (email or phone) and password."""
        identifier = req.identifier.strip()
        user: UserInDB | None = None

        if "@" in identifier:
            user = await self.user_repo.get_by_email(normalize_email(identifier) or "")
        else:
            user = await self.user_repo.get_by_phone(normalize_phone(identifier) or "")

        if not user or not user.password_hash:
            raise UnauthorizedException(
                message="Invalid email/phone or password",
                code=ErrorCode.AUTH_INVALID_CREDENTIALS,
            )

        if not verify_password(req.password, user.password_hash):
            raise UnauthorizedException(
                message="Invalid email/phone or password",
                code=ErrorCode.AUTH_INVALID_CREDENTIALS,
            )

        if user.status != UserStatus.ACTIVE:
            raise ForbiddenException(
                message="Account is inactive or suspended. Please contact support.",
                code=ErrorCode.AUTH_ACCOUNT_INACTIVE,
            )

        now = utc_now()
        await self.user_repo.update(user.id, {"last_login_at": now})
        user.last_login_at = now

        return await self._issue_tokens(user, user_agent=user_agent, ip_address=ip_address)

    async def send_otp(self, req: SendOtpRequest) -> SendOtpResponse:
        """Dispatch a 4-digit numeric OTP to the specified phone number."""
        phone = req.phone
        latest_otp = await self.auth_repo.get_latest_otp(phone)
        now = utc_now()

        if latest_otp and now < latest_otp.cooldown_until:
            wait_seconds = int((latest_otp.cooldown_until - now).total_seconds()) + 1
            raise RateLimitedException(
                message=f"Please wait {wait_seconds} seconds before requesting a new OTP code",
                code=ErrorCode.AUTH_OTP_RATE_LIMITED,
                details={"cooldown_seconds": wait_seconds},
            )

        otp_code = generate_secure_otp(length=self.settings.otp_length)
        otp_hash = hash_otp(otp_code, self.settings.jwt_secret_key)
        cooldown_delta = timedelta(seconds=self.settings.otp_resend_cooldown_seconds)
        expires_delta = timedelta(seconds=self.settings.otp_expire_seconds)

        otp_doc = OtpDocument(
            id=str(uuid.uuid4()),
            phone=phone,
            otp_hash=otp_hash,
            channel=req.channel,
            status=OtpStatus.PENDING,
            attempts=0,
            cooldown_until=now + cooldown_delta,
            expires_at=now + expires_delta,
            created_at=now,
        )
        await self.auth_repo.create_otp(otp_doc)

        await self.otp_provider.send_otp(phone, otp_code, req.channel)

        return SendOtpResponse(
            phone=phone,
            channel=req.channel,
            cooldown_seconds=self.settings.otp_resend_cooldown_seconds,
            expires_in=self.settings.otp_expire_seconds,
        )

    async def verify_otp(
        self,
        req: VerifyOtpRequest,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> TokenResponse:
        """Verify candidate OTP, creating user account if non-existent, and returning tokens."""
        phone = req.phone
        latest_otp = await self.auth_repo.get_latest_otp(phone)
        now = utc_now()

        if not latest_otp or latest_otp.status != OtpStatus.PENDING:
            raise BadRequestException(
                message="No active OTP verification session found. Please request a new code.",
                code=ErrorCode.AUTH_INVALID_OTP,
            )

        if now > latest_otp.expires_at:
            raise BadRequestException(
                message="The OTP code has expired. Please request a new code.",
                code=ErrorCode.AUTH_OTP_EXPIRED,
            )

        if latest_otp.attempts >= self.settings.otp_max_attempts:
            raise BadRequestException(
                message="Maximum verification attempts exceeded. Please request a new code.",
                code=ErrorCode.AUTH_OTP_MAX_ATTEMPTS,
            )

        if not verify_otp_hash(req.otp, latest_otp.otp_hash, self.settings.jwt_secret_key):
            new_attempts = await self.auth_repo.increment_otp_attempts(latest_otp.id)
            remaining = max(0, self.settings.otp_max_attempts - new_attempts)
            raise BadRequestException(
                message=f"Invalid OTP code. {remaining} attempt(s) remaining.",
                code=ErrorCode.AUTH_INVALID_OTP,
                details={"remaining_attempts": remaining},
            )

        await self.auth_repo.mark_otp_verified(latest_otp.id)

        user = await self.user_repo.get_by_phone(phone)
        if not user:
            # Auto-signup user Oppam style
            user_id = str(uuid.uuid4())
            user = UserInDB(
                id=user_id,
                first_name="User",
                last_name=phone[-4:],
                phone=phone,
                roles=[UserRole.USER],
                status=UserStatus.ACTIVE,
                is_verified=True,
                auth_providers=[AuthProvider.OTP],
                created_at=now,
                updated_at=now,
                last_login_at=now,
            )
            await self.user_repo.create(user)
        else:
            if user.status != UserStatus.ACTIVE:
                raise ForbiddenException(
                    message="Account is inactive or suspended. Please contact support.",
                    code=ErrorCode.AUTH_ACCOUNT_INACTIVE,
                )

            updates: dict[str, Any] = {"last_login_at": now}
            if not user.is_verified:
                updates["is_verified"] = True
                user.is_verified = True
            if AuthProvider.OTP not in user.auth_providers:
                updated_providers = list(user.auth_providers) + [AuthProvider.OTP]
                updates["auth_providers"] = updated_providers
                user.auth_providers = updated_providers

            await self.user_repo.update(user.id, updates)
            user.last_login_at = now

        return await self._issue_tokens(user, user_agent=user_agent, ip_address=ip_address)

    async def refresh_token(
        self,
        refresh_token_str: str,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> TokenResponse:
        """Rotate refresh token and issue a fresh access/refresh token pair."""
        payload = decode_jwt_token(
            token=refresh_token_str,
            secret_key=self.settings.jwt_secret_key,
            algorithm=self.settings.jwt_algorithm,
        )

        if payload.get("token_type") != TokenType.REFRESH:
            raise UnauthorizedException(
                message="Invalid token type provided for refresh flow",
                code=ErrorCode.AUTH_REFRESH_TOKEN_INVALID,
            )

        jti = payload.get("jti")
        user_id = payload.get("sub")

        if not jti or not user_id:
            raise UnauthorizedException(
                message="Malformed token claims",
                code=ErrorCode.AUTH_REFRESH_TOKEN_INVALID,
            )

        session = await self.auth_repo.get_refresh_session(jti)
        if not session or session.is_revoked:
            if session and session.is_revoked:
                # Potential token reuse attack! Revoke all sessions for this user
                logger.warning(
                    f"Revoked refresh token reused for user {user_id}. Revoking all sessions."
                )
                await self.auth_repo.revoke_all_user_refresh_sessions(user_id)
            raise UnauthorizedException(
                message="Refresh session has been revoked or expired",
                code=ErrorCode.AUTH_REFRESH_TOKEN_INVALID,
            )

        # Invalidate old refresh session (Rotation)
        await self.auth_repo.revoke_refresh_session(jti)

        user = await self.user_repo.get_by_id(user_id)
        if not user or user.status != UserStatus.ACTIVE:
            raise UnauthorizedException(
                message="User account no longer active",
                code=ErrorCode.AUTH_ACCOUNT_INACTIVE,
            )

        return await self._issue_tokens(user, user_agent=user_agent, ip_address=ip_address)

    async def logout(
        self, refresh_token_str: str | None = None, user_id: str | None = None
    ) -> None:
        """Revoke active refresh token session."""
        if refresh_token_str:
            try:
                payload = decode_jwt_token(
                    token=refresh_token_str,
                    secret_key=self.settings.jwt_secret_key,
                    algorithm=self.settings.jwt_algorithm,
                )
                jti = payload.get("jti")
                if jti:
                    await self.auth_repo.revoke_refresh_session(jti)
            except Exception:
                pass

        if user_id and not refresh_token_str:
            await self.auth_repo.revoke_all_user_refresh_sessions(user_id)

    async def _issue_tokens(
        self,
        user: UserInDB,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> TokenResponse:
        """Mint signed JWT access token and persist a rotated refresh token session."""
        access_delta = timedelta(minutes=self.settings.jwt_access_token_expire_minutes)
        refresh_delta = timedelta(days=self.settings.jwt_refresh_token_expire_days)

        access_payload = {
            "sub": user.id,
            "roles": [r.value for r in user.roles],
            "token_type": TokenType.ACCESS,
            "email": user.email,
            "phone": user.phone,
        }
        access_token = create_jwt_token(
            payload=access_payload,
            expires_delta=access_delta,
            secret_key=self.settings.jwt_secret_key,
            algorithm=self.settings.jwt_algorithm,
        )

        refresh_jti = str(uuid.uuid4())
        refresh_payload = {
            "sub": user.id,
            "jti": refresh_jti,
            "token_type": TokenType.REFRESH,
        }
        refresh_token = create_jwt_token(
            payload=refresh_payload,
            expires_delta=refresh_delta,
            secret_key=self.settings.jwt_secret_key,
            algorithm=self.settings.jwt_algorithm,
        )

        now = utc_now()
        session_doc = RefreshSessionDocument(
            id=refresh_jti,
            user_id=user.id,
            token_hash=hash_otp(refresh_token, self.settings.jwt_secret_key),
            is_revoked=False,
            user_agent=user_agent,
            ip_address=ip_address,
            created_at=now,
            expires_at=now + refresh_delta,
        )
        await self.auth_repo.create_refresh_session(session_doc)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.settings.jwt_access_token_expire_minutes * 60,
            user=UserProfileResponse.from_user_db(user),
        )
