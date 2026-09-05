"""FastAPI router for Therapist discovery and management endpoints."""

from fastapi import APIRouter, Depends, Query

from app.common.pagination.pagination import PaginatedData
from app.common.responses.api_response import ApiResponse
from app.modules.auth.auth_dependency import get_current_active_user, require_roles
from app.modules.therapist.therapist_constants import (
    SessionMode,
    TherapistSortBy,
    TherapistSpecialization,
    TherapistStatus,
)
from app.modules.therapist.therapist_controller import TherapistController
from app.modules.therapist.therapist_dependency import (
    get_optional_current_user,
    get_therapist_service,
)
from app.modules.therapist.therapist_schema import (
    AdminUpdateTherapistVerificationRequest,
    CreateTherapistRequest,
    TherapistDetailResponse,
    TherapistSummaryResponse,
    UpdateTherapistRequest,
)
from app.modules.therapist.therapist_service import TherapistService
from app.modules.user.user_constants import UserRole
from app.modules.user.user_model import UserInDB

router = APIRouter(prefix="/therapists", tags=["Therapists"])


def get_therapist_controller(
    service: TherapistService = Depends(get_therapist_service),
) -> TherapistController:
    """Dependency injecting configured TherapistController."""
    return TherapistController(therapist_service=service)


@router.get(
    "",
    response_model=ApiResponse[PaginatedData[TherapistSummaryResponse]],
    summary="Discover and list verified therapists",
)
async def list_therapists(
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=10, ge=1, le=50, description="Items per page"),
    search: str | None = Query(default=None, description="Search term for name or designation"),
    language: str | None = Query(
        default=None, description="Language code filter (e.g. 'en', 'ml', 'ta')"
    ),
    specialization: TherapistSpecialization | None = Query(
        default=None, description="Clinical specialization"
    ),
    expertise: str | None = Query(
        default=None, description="Specific concern or area of expertise"
    ),
    session_mode: SessionMode | None = Query(default=None, description="Session delivery mode"),
    status: TherapistStatus | None = Query(
        default=None, description="Operational status (Staff/Admin only)"
    ),
    sort: TherapistSortBy = Query(
        default=TherapistSortBy.RELEVANCE, description="Sorting parameter"
    ),
    caller: UserInDB | None = Depends(get_optional_current_user),
    controller: TherapistController = Depends(get_therapist_controller),
) -> ApiResponse[PaginatedData[TherapistSummaryResponse]]:
    """Public discovery endpoint returning paginated therapist profiles matching criteria."""
    return await controller.list_therapists(
        page=page,
        limit=limit,
        search=search,
        language=language,
        specialization=specialization,
        expertise=expertise,
        session_mode=session_mode,
        status=status,
        sort=sort,
        caller=caller,
    )


@router.get(
    "/me",
    response_model=ApiResponse[TherapistDetailResponse],
    summary="Get current authenticated therapist's profile",
)
async def get_my_profile(
    caller: UserInDB = Depends(get_current_active_user),
    controller: TherapistController = Depends(get_therapist_controller),
) -> ApiResponse[TherapistDetailResponse]:
    """Retrieve profile of the logged-in therapist."""
    return await controller.get_my_profile(caller=caller)


@router.get(
    "/{therapist_id}",
    response_model=ApiResponse[TherapistDetailResponse],
    summary="Retrieve detailed therapist profile",
)
async def get_therapist_detail(
    therapist_id: str,
    caller: UserInDB | None = Depends(get_optional_current_user),
    controller: TherapistController = Depends(get_therapist_controller),
) -> ApiResponse[TherapistDetailResponse]:
    """Public detail view for active/verified therapists, or authorized private view."""
    return await controller.get_therapist_detail(therapist_id=therapist_id, caller=caller)


@router.post(
    "",
    response_model=ApiResponse[TherapistDetailResponse],
    status_code=201,
    summary="Create a new therapist profile",
)
async def create_therapist(
    req: CreateTherapistRequest,
    caller: UserInDB = Depends(get_current_active_user),
    controller: TherapistController = Depends(get_therapist_controller),
) -> ApiResponse[TherapistDetailResponse]:
    """Create a therapist profile attached to the authenticated account."""
    return await controller.create_therapist(caller=caller, req=req)


@router.patch(
    "/{therapist_id}",
    response_model=ApiResponse[TherapistDetailResponse],
    summary="Update therapist profile",
)
async def update_therapist(
    therapist_id: str,
    req: UpdateTherapistRequest,
    caller: UserInDB = Depends(get_current_active_user),
    controller: TherapistController = Depends(get_therapist_controller),
) -> ApiResponse[TherapistDetailResponse]:
    """Update profile attributes. Restricted to the therapist owner or administrators."""
    return await controller.update_therapist(therapist_id=therapist_id, caller=caller, req=req)


@router.patch(
    "/{therapist_id}/verification",
    response_model=ApiResponse[TherapistDetailResponse],
    summary="Update administrative verification status",
)
async def update_verification(
    therapist_id: str,
    req: AdminUpdateTherapistVerificationRequest,
    admin_user: UserInDB = Depends(
        require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.STAFF)
    ),
    controller: TherapistController = Depends(get_therapist_controller),
) -> ApiResponse[TherapistDetailResponse]:
    """Approve or reject therapist credentials. Restricted to administrators and staff."""
    return await controller.update_verification(
        therapist_id=therapist_id,
        admin_user=admin_user,
        req=req,
    )
