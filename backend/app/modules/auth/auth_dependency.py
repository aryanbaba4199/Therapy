"""FastAPI dependencies for authentication, token parsing, and role-based access control."""

from collections.abc import Callable
from typing import Any

from fastapi import Depends, Header
from fastapi.security import OAuth2PasswordBearer
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.common.exceptions.app_exceptions import ForbiddenException, UnauthorizedException
from app.common.exceptions.error_codes import ErrorCode
from app.core.config import Settings, get_settings
from app.database.mongodb import get_database
from app.modules.auth.auth_constants import TokenType
from app.modules.auth.auth_repository import AuthRepository
from app.modules.auth.auth_service import AuthService
from app.modules.auth.auth_utils import decode_jwt_token
from app.modules.user.user_constants import UserRole, UserStatus
from app.modules.user.user_dependency import get_user_repository
from app.modules.user.user_model import UserInDB
from app.modules.user.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_auth_repository(
    db: AsyncIOMotorDatabase[dict[str, Any]] = Depends(get_database),
) -> AuthRepository:
    """Dependency injecting AuthRepository."""
    return AuthRepository(db)


def get_auth_service(
    user_repo: UserRepository = Depends(get_user_repository),
    auth_repo: AuthRepository = Depends(get_auth_repository),
    settings: Settings = Depends(get_settings),
) -> AuthService:
    """Dependency injecting configured AuthService."""
    return AuthService(user_repo=user_repo, auth_repo=auth_repo, settings=settings)


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    auth_header: str | None = Header(None, alias="Authorization"),
    user_repo: UserRepository = Depends(get_user_repository),
    settings: Settings = Depends(get_settings),
) -> UserInDB:
    """Extract and validate JWT access token, resolving to current User entity."""
    raw_token = token
    if not raw_token and auth_header and auth_header.startswith("Bearer "):
        raw_token = auth_header[7:].strip()

    if not raw_token:
        raise UnauthorizedException(
            message="Authentication credentials were not provided",
            code=ErrorCode.UNAUTHORIZED,
        )

    payload = decode_jwt_token(
        token=raw_token,
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    if payload.get("token_type") != TokenType.ACCESS:
        raise UnauthorizedException(
            message="Provided token is not an access token",
            code=ErrorCode.AUTH_INVALID_TOKEN,
        )

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException(
            message="Token subject is missing",
            code=ErrorCode.AUTH_INVALID_TOKEN,
        )

    user = await user_repo.get_by_id(user_id)
    if not user:
        raise UnauthorizedException(
            message="User associated with token no longer exists",
            code=ErrorCode.USER_NOT_FOUND,
        )

    return user


async def get_current_active_user(
    current_user: UserInDB = Depends(get_current_user),
) -> UserInDB:
    """Ensure the authenticated user is in ACTIVE status."""
    if current_user.status != UserStatus.ACTIVE:
        raise ForbiddenException(
            message="User account is inactive or suspended",
            code=ErrorCode.AUTH_ACCOUNT_INACTIVE,
        )
    return current_user


def require_roles(*allowed_roles: UserRole) -> Callable[..., Any]:
    """Dependency factory enforcing role-based access control."""

    async def role_checker(
        current_user: UserInDB = Depends(get_current_active_user),
    ) -> UserInDB:
        user_roles = set(current_user.roles)
        # SUPER_ADMIN bypasses role checks
        if UserRole.SUPER_ADMIN in user_roles:
            return current_user

        if not any(role in user_roles for role in allowed_roles):
            role_names = [r.value for r in allowed_roles]
            raise ForbiddenException(
                message=f"Access denied. Requires one of roles: {role_names}",
                code=ErrorCode.FORBIDDEN,
            )
        return current_user

    return role_checker
