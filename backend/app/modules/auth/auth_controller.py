"""HTTP presentation controller for authentication endpoints."""

from fastapi import Request, Response

from app.common.exceptions.app_exceptions import UnauthorizedException
from app.common.exceptions.error_codes import ErrorCode
from app.common.responses.api_response import ApiResponse, success_response
from app.core.config import Settings
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


class AuthController:
    """Handles HTTP requests, cookie management, and response formatting for auth."""

    def __init__(self, auth_service: AuthService, settings: Settings) -> None:
        self.auth_service = auth_service
        self.settings = settings

    def _set_refresh_cookie(self, response: Response, refresh_token: str) -> None:
        """Attach secure HttpOnly cookie containing refresh token to response."""
        response.set_cookie(
            key=self.settings.refresh_cookie_name,
            value=refresh_token,
            max_age=self.settings.jwt_refresh_token_expire_days * 86400,
            httponly=self.settings.refresh_cookie_httponly,
            secure=self.settings.refresh_cookie_secure,
            samesite=self.settings.refresh_cookie_samesite,
            domain=self.settings.refresh_cookie_domain,
            path=self.settings.refresh_cookie_path,
        )

    def _clear_refresh_cookie(self, response: Response) -> None:
        """Clear refresh token cookie."""
        response.delete_cookie(
            key=self.settings.refresh_cookie_name,
            domain=self.settings.refresh_cookie_domain,
            path=self.settings.refresh_cookie_path,
        )

    def _extract_client_info(self, request: Request) -> tuple[str | None, str | None]:
        """Extract User-Agent and Client IP safely from HTTP request."""
        from app.common.utils.request_utils import get_client_ip

        user_agent = request.headers.get("user-agent")
        trusted_proxies = getattr(self.settings, "trusted_proxies", None)
        ip = get_client_ip(request, trusted_proxies)
        return user_agent, ip

    async def register(
        self,
        req: RegisterRequest,
        request: Request,
        response: Response,
    ) -> ApiResponse[TokenResponse]:
        """Register new user and issue authentication tokens."""
        user_agent, ip = self._extract_client_info(request)
        tokens = await self.auth_service.register(req, user_agent=user_agent, ip_address=ip)
        if tokens.refresh_token:
            self._set_refresh_cookie(response, tokens.refresh_token)
        return success_response(data=tokens, message="Registration successful")

    async def login(
        self,
        req: LoginRequest,
        request: Request,
        response: Response,
    ) -> ApiResponse[TokenResponse]:
        """Authenticate user and issue authentication tokens."""
        user_agent, ip = self._extract_client_info(request)
        tokens = await self.auth_service.login(req, user_agent=user_agent, ip_address=ip)
        if tokens.refresh_token:
            self._set_refresh_cookie(response, tokens.refresh_token)
        return success_response(data=tokens, message="Login successful")

    async def send_otp(self, req: SendOtpRequest) -> ApiResponse[SendOtpResponse]:
        """Dispatch numeric OTP code to phone number."""
        otp_meta = await self.auth_service.send_otp(req)
        return success_response(data=otp_meta, message="OTP code sent successfully")

    async def verify_otp(
        self,
        req: VerifyOtpRequest,
        request: Request,
        response: Response,
    ) -> ApiResponse[TokenResponse]:
        """Verify numeric OTP code and issue tokens."""
        user_agent, ip = self._extract_client_info(request)
        tokens = await self.auth_service.verify_otp(req, user_agent=user_agent, ip_address=ip)
        if tokens.refresh_token:
            self._set_refresh_cookie(response, tokens.refresh_token)
        return success_response(data=tokens, message="Verification successful")

    async def refresh_token(
        self,
        req: RefreshTokenRequest,
        request: Request,
        response: Response,
    ) -> ApiResponse[TokenResponse]:
        """Rotate refresh token using cookie or body value."""
        token_str = req.refresh_token or request.cookies.get(self.settings.refresh_cookie_name)
        if not token_str:
            raise UnauthorizedException(
                message="Refresh token was not provided in request cookie or body",
                code=ErrorCode.AUTH_REFRESH_TOKEN_INVALID,
            )

        user_agent, ip = self._extract_client_info(request)
        tokens = await self.auth_service.refresh_token(
            token_str, user_agent=user_agent, ip_address=ip
        )
        if tokens.refresh_token:
            self._set_refresh_cookie(response, tokens.refresh_token)
        return success_response(data=tokens, message="Token refreshed successfully")

    async def logout(
        self,
        request: Request,
        response: Response,
        current_user: UserInDB | None = None,
    ) -> ApiResponse[dict[str, str]]:
        """Invalidate session and delete refresh cookie."""
        token_str = request.cookies.get(self.settings.refresh_cookie_name)
        user_id = current_user.id if current_user else None
        await self.auth_service.logout(refresh_token_str=token_str, user_id=user_id)
        self._clear_refresh_cookie(response)
        return success_response(data={"status": "logged_out"}, message="Logged out successfully")

    async def get_me(self, current_user: UserInDB) -> ApiResponse[UserProfileResponse]:
        """Return profile information of current authenticated user."""
        profile = UserProfileResponse.from_user_db(current_user)
        return success_response(data=profile)
