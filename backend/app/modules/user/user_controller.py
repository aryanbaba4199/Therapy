"""HTTP presentation controller for User endpoints."""

from app.common.responses.api_response import ApiResponse, success_response
from app.modules.user.user_model import UserInDB
from app.modules.user.user_schema import UserProfileResponse, UserUpdateProfileRequest
from app.modules.user.user_service import UserService


class UserController:
    """Handles HTTP requests and response envelopes for user profile operations."""

    def __init__(self, user_service: UserService) -> None:
        self.user_service = user_service

    async def get_profile(self, current_user: UserInDB) -> ApiResponse[UserProfileResponse]:
        """Fetch current user's profile."""
        profile = await self.user_service.get_profile(current_user.id)
        return success_response(data=profile)

    async def update_profile(
        self, current_user: UserInDB, req: UserUpdateProfileRequest
    ) -> ApiResponse[UserProfileResponse]:
        """Update current user's profile details."""
        updated = await self.user_service.update_profile(current_user.id, req)
        return success_response(data=updated, message="Profile updated successfully")
