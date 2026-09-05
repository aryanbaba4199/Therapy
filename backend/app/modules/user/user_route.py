"""FastAPI router for user profile operations."""

from fastapi import APIRouter, Depends

from app.common.responses.api_response import ApiResponse
from app.modules.auth.auth_dependency import get_current_active_user
from app.modules.user.user_controller import UserController
from app.modules.user.user_dependency import get_user_service
from app.modules.user.user_model import UserInDB
from app.modules.user.user_schema import UserProfileResponse, UserUpdateProfileRequest
from app.modules.user.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


def get_user_controller(
    user_service: UserService = Depends(get_user_service),
) -> UserController:
    """Dependency injecting configured UserController."""
    return UserController(user_service=user_service)


@router.get(
    "/me",
    response_model=ApiResponse[UserProfileResponse],
    summary="Retrieve current user's profile",
)
async def get_my_profile(
    current_user: UserInDB = Depends(get_current_active_user),
    controller: UserController = Depends(get_user_controller),
) -> ApiResponse[UserProfileResponse]:
    """Return profile attributes for the authenticated user."""
    return await controller.get_profile(current_user)


@router.patch(
    "/me",
    response_model=ApiResponse[UserProfileResponse],
    summary="Update current user's profile",
)
async def update_my_profile(
    req: UserUpdateProfileRequest,
    current_user: UserInDB = Depends(get_current_active_user),
    controller: UserController = Depends(get_user_controller),
) -> ApiResponse[UserProfileResponse]:
    """Modify name, preferences, or profile metadata for the authenticated user."""
    return await controller.update_profile(current_user, req)
