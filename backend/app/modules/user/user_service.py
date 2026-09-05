"""Domain business logic for user management."""

from app.common.exceptions.app_exceptions import NotFoundException
from app.common.exceptions.error_codes import ErrorCode
from app.modules.user.user_repository import UserRepository
from app.modules.user.user_schema import UserProfileResponse, UserUpdateProfileRequest


class UserService:
    """Handles business logic and data mapping for Users."""

    def __init__(self, user_repo: UserRepository) -> None:
        self.user_repo = user_repo

    async def get_profile(self, user_id: str) -> UserProfileResponse:
        """Fetch user profile or raise NotFoundException."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException(
                message="User profile not found",
                code=ErrorCode.USER_NOT_FOUND,
            )
        return UserProfileResponse.from_user_db(user)

    async def update_profile(
        self, user_id: str, req: UserUpdateProfileRequest
    ) -> UserProfileResponse:
        """Apply profile modifications and return updated view."""
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException(
                message="User profile not found",
                code=ErrorCode.USER_NOT_FOUND,
            )

        update_dict = req.model_dump(exclude_unset=True)
        if not update_dict:
            return UserProfileResponse.from_user_db(user)

        updated_user = await self.user_repo.update(user_id, update_dict)
        if not updated_user:
            raise NotFoundException(
                message="User profile not found after update",
                code=ErrorCode.USER_NOT_FOUND,
            )
        return UserProfileResponse.from_user_db(updated_user)
