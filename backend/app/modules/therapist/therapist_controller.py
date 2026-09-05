"""HTTP presentation controller for Therapist endpoints."""

from app.common.pagination.pagination import PaginatedData, PaginationParams
from app.common.responses.api_response import ApiResponse, success_response
from app.modules.therapist.therapist_constants import (
    SessionMode,
    TherapistSortBy,
    TherapistSpecialization,
    TherapistStatus,
)
from app.modules.therapist.therapist_schema import (
    AdminUpdateTherapistVerificationRequest,
    CreateTherapistRequest,
    TherapistDetailResponse,
    TherapistSummaryResponse,
    UpdateTherapistRequest,
)
from app.modules.therapist.therapist_service import TherapistService
from app.modules.user.user_model import UserInDB


class TherapistController:
    """Handles HTTP requests, parameter extraction, and response envelopes for therapists."""

    def __init__(self, therapist_service: TherapistService) -> None:
        self.therapist_service = therapist_service

    async def list_therapists(
        self,
        page: int,
        limit: int,
        search: str | None,
        language: str | None,
        specialization: TherapistSpecialization | None,
        expertise: str | None,
        session_mode: SessionMode | None,
        status: TherapistStatus | None,
        sort: TherapistSortBy,
        caller: UserInDB | None,
    ) -> ApiResponse[PaginatedData[TherapistSummaryResponse]]:
        """List and paginate therapists based on discovery query parameters."""
        pagination = PaginationParams(page=page, limit=limit)
        data = await self.therapist_service.list_therapists(
            pagination=pagination,
            search=search,
            language=language,
            specialization=specialization,
            expertise=expertise,
            session_mode=session_mode,
            status=status,
            sort=sort,
            caller=caller,
        )
        return success_response(data=data)

    async def get_therapist_detail(
        self,
        therapist_id: str,
        caller: UserInDB | None,
    ) -> ApiResponse[TherapistDetailResponse]:
        """Fetch detailed therapist profile."""
        data = await self.therapist_service.get_therapist_detail(
            therapist_id=therapist_id,
            caller=caller,
        )
        return success_response(data=data)

    async def get_my_profile(
        self,
        caller: UserInDB,
    ) -> ApiResponse[TherapistDetailResponse]:
        """Fetch therapist profile belonging to current authenticated user."""
        data = await self.therapist_service.get_my_profile(caller=caller)
        return success_response(data=data)

    async def create_therapist(
        self,
        caller: UserInDB,
        req: CreateTherapistRequest,
    ) -> ApiResponse[TherapistDetailResponse]:
        """Create a new therapist profile."""
        data = await self.therapist_service.create_therapist(caller=caller, req=req)
        return success_response(data=data, message="Therapist profile created successfully")

    async def update_therapist(
        self,
        therapist_id: str,
        caller: UserInDB,
        req: UpdateTherapistRequest,
    ) -> ApiResponse[TherapistDetailResponse]:
        """Update existing therapist profile."""
        data = await self.therapist_service.update_therapist(
            therapist_id=therapist_id,
            caller=caller,
            req=req,
        )
        return success_response(data=data, message="Therapist profile updated successfully")

    async def update_verification(
        self,
        therapist_id: str,
        admin_user: UserInDB,
        req: AdminUpdateTherapistVerificationRequest,
    ) -> ApiResponse[TherapistDetailResponse]:
        """Update administrative verification status."""
        data = await self.therapist_service.update_verification(
            therapist_id=therapist_id,
            admin_user=admin_user,
            req=req,
        )
        return success_response(data=data, message="Verification status updated successfully")
