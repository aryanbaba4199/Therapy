"""FastAPI router for authentication and session management endpoints."""

from fastapi import APIRouter, Depends, Request, Response

from app.common.responses.api_response import ApiResponse
from app.core.config import Settings, get_settings
from app.core.rate_limiter import RateLimiter
from app.modules.auth.auth_controller import AuthController
from app.modules.auth.auth_dependency import (
    get_auth_service,
    get_current_active_user,
    get_current_user,
)
from app.modules.auth.auth_schema import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    SendOtpRequest,
    SendOtpResponse,
    TokenResponse,
    VerifyOtpRequest,
)
from app.modules.auth.auth_service import AuthService
from app.modules.user.user_model import UserInDB
from app.modules.user.user_schema import UserProfileResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_auth_controller(
    auth_service: AuthService = Depends(get_auth_service),
    settings: Settings = Depends(get_settings),
) -> AuthController:
    """Dependency injecting configured AuthController."""
    return AuthController(auth_service=auth_service, settings=settings)


@router.post(
    "/register",
    response_model=ApiResponse[TokenResponse],
    status_code=201,
    summary="Register a new user account",
)
async def register(
    req: RegisterRequest,
    request: Request,
    response: Response,
    controller: AuthController = Depends(get_auth_controller),
) -> ApiResponse[TokenResponse]:
    """Register user with email/phone and password, returning tokens and profile."""
    return await controller.register(req, request, response)


@router.post(
    "/login",
    response_model=ApiResponse[TokenResponse],
    summary="Authenticate with credentials",
    dependencies=[Depends(RateLimiter(times=10, seconds=60, action="auth_login"))],
)
async def login(
    req: LoginRequest,
    request: Request,
    response: Response,
    controller: AuthController = Depends(get_auth_controller),
) -> ApiResponse[TokenResponse]:
    """Authenticate with identifier (email or phone) and password."""
    return await controller.login(req, request, response)


@router.post(
    "/otp/send",
    response_model=ApiResponse[SendOtpResponse],
    summary="Send OTP verification code to phone number",
    dependencies=[Depends(RateLimiter(times=5, seconds=60, action="auth_otp_send"))],
)
async def send_otp(
    req: SendOtpRequest,
    controller: AuthController = Depends(get_auth_controller),
) -> ApiResponse[SendOtpResponse]:
    """Request a numeric OTP code dispatched to phone via WhatsApp or SMS."""
    return await controller.send_otp(req)


@router.post(
    "/otp/verify",
    response_model=ApiResponse[TokenResponse],
    summary="Verify phone OTP code and login/signup",
    dependencies=[Depends(RateLimiter(times=10, seconds=60, action="auth_otp_verify"))],
)
async def verify_otp(
    req: VerifyOtpRequest,
    request: Request,
    response: Response,
    controller: AuthController = Depends(get_auth_controller),
) -> ApiResponse[TokenResponse]:
    """Verify numeric OTP code. Creates user if new, otherwise logs in."""
    return await controller.verify_otp(req, request, response)


@router.post(
    "/refresh",
    response_model=ApiResponse[TokenResponse],
    summary="Rotate refresh token to obtain a fresh access token",
    dependencies=[Depends(RateLimiter(times=30, seconds=60, action="auth_refresh"))],
)
async def refresh_token(
    req: RefreshTokenRequest,
    request: Request,
    response: Response,
    controller: AuthController = Depends(get_auth_controller),
) -> ApiResponse[TokenResponse]:
    """Exchange refresh token (from cookie or payload) for rotated token pair."""
    return await controller.refresh_token(req, request, response)


@router.post(
    "/logout",
    response_model=ApiResponse[dict[str, str]],
    summary="Revoke active session and clear authentication cookies",
)
async def logout(
    request: Request,
    response: Response,
    current_user: UserInDB | None = Depends(get_current_user),
    controller: AuthController = Depends(get_auth_controller),
) -> ApiResponse[dict[str, str]]:
    """Log out current user and revoke their refresh session."""
    return await controller.logout(request, response, current_user=current_user)


@router.get(
    "/me",
    response_model=ApiResponse[UserProfileResponse],
    summary="Retrieve current authenticated user profile",
)
async def get_me(
    current_user: UserInDB = Depends(get_current_active_user),
    controller: AuthController = Depends(get_auth_controller),
) -> ApiResponse[UserProfileResponse]:
    """Fetch profile data of authenticated identity from bearer token."""
    return await controller.get_me(current_user)
