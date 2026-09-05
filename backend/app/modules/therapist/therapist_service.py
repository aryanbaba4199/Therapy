"""Business logic and domain workflow management for Therapists."""

import re
import uuid
from typing import Any

from app.common.exceptions.app_exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.common.exceptions.error_codes import ErrorCode
from app.common.pagination.pagination import PaginatedData, PaginationMeta, PaginationParams
from app.common.utils.datetime_utils import utc_now
from app.modules.therapist.therapist_constants import (
    VALID_STATUS_TRANSITIONS,
    SessionMode,
    TherapistSortBy,
    TherapistSpecialization,
    TherapistStatus,
    TherapistVerificationStatus,
)
from app.modules.therapist.therapist_model import (
    PricingModel,
    TherapistInDB,
    VerificationModel,
)
from app.modules.therapist.therapist_repository import TherapistRepository
from app.modules.therapist.therapist_schema import (
    AdminUpdateTherapistVerificationRequest,
    CreateTherapistRequest,
    TherapistDetailResponse,
    TherapistSummaryResponse,
    UpdateTherapistRequest,
)
from app.modules.user.user_constants import UserRole
from app.modules.user.user_model import UserInDB
from app.modules.user.user_repository import UserRepository


class TherapistService:
    """Core domain service for therapist discovery, profiles, and verification."""

    def __init__(
        self,
        therapist_repo: TherapistRepository,
        user_repo: UserRepository,
    ) -> None:
        self.therapist_repo = therapist_repo
        self.user_repo = user_repo

    async def list_therapists(
        self,
        pagination: PaginationParams,
        search: str | None = None,
        language: str | None = None,
        specialization: TherapistSpecialization | None = None,
        expertise: str | None = None,
        session_mode: SessionMode | None = None,
        status: TherapistStatus | None = None,
        sort: TherapistSortBy = TherapistSortBy.RELEVANCE,
        caller: UserInDB | None = None,
    ) -> PaginatedData[TherapistSummaryResponse]:
        """Query and paginate therapists with discovery filters."""
        filter_query: dict[str, Any] = {}

        is_admin_or_staff = caller is not None and any(
            r in caller.roles for r in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.STAFF]
        )

        # Public discovery default: active and verified only
        if not is_admin_or_staff:
            filter_query["status"] = TherapistStatus.ACTIVE
            filter_query["verification.status"] = TherapistVerificationStatus.VERIFIED
        else:
            if status is not None:
                filter_query["status"] = status.value

        if language:
            filter_query["languages"] = language.strip().lower()

        if specialization:
            filter_query["specialization"] = specialization.value

        if expertise:
            filter_query["expertises"] = expertise.strip().lower()

        if session_mode:
            filter_query["session_modes"] = session_mode.value

        if search and search.strip():
            safe_search = re.escape(search.strip())
            regex_pat = {"$regex": safe_search, "$options": "i"}
            filter_query["$or"] = [
                {"display_name": regex_pat},
                {"first_name": regex_pat},
                {"last_name": regex_pat},
                {"designation": regex_pat},
                {"expertises": regex_pat},
            ]

        docs, total_count = await self.therapist_repo.find_paginated(
            filter_query=filter_query,
            sort_by=sort,
            skip=pagination.skip,
            limit=pagination.limit,
        )

        items = [TherapistSummaryResponse.from_therapist_db(doc) for doc in docs]
        meta = PaginationMeta.create(
            page=pagination.page,
            limit=pagination.limit,
            total_items=total_count,
        )
        return PaginatedData(items=items, pagination=meta)

    async def get_therapist_detail(
        self, therapist_id: str, caller: UserInDB | None = None
    ) -> TherapistDetailResponse:
        """Fetch detailed therapist profile with access control check."""
        therapist = await self.therapist_repo.get_by_id(therapist_id)
        if not therapist:
            raise NotFoundException(
                message="Therapist not found",
                code=ErrorCode.THERAPIST_NOT_FOUND,
            )

        # Active & verified profiles are public
        is_public_ready = (
            therapist.status == TherapistStatus.ACTIVE
            and therapist.verification.status == TherapistVerificationStatus.VERIFIED
        )

        if not is_public_ready:
            is_owner = caller is not None and caller.id == therapist.user_id
            is_privileged = caller is not None and any(
                r in caller.roles for r in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.STAFF]
            )
            if not is_owner and not is_privileged:
                raise NotFoundException(
                    message="Therapist profile not found or unavailable",
                    code=ErrorCode.THERAPIST_NOT_FOUND,
                )

        return TherapistDetailResponse.from_therapist_db(therapist)

    async def get_my_profile(self, caller: UserInDB) -> TherapistDetailResponse:
        """Retrieve therapist profile belonging to authenticated user."""
        therapist = await self.therapist_repo.get_by_user_id(caller.id)
        if not therapist:
            raise NotFoundException(
                message="No therapist profile associated with current account",
                code=ErrorCode.THERAPIST_NOT_FOUND,
            )
        return TherapistDetailResponse.from_therapist_db(therapist)

    async def create_therapist(
        self, caller: UserInDB, req: CreateTherapistRequest
    ) -> TherapistDetailResponse:
        """Create a new therapist profile for current user."""
        existing = await self.therapist_repo.get_by_user_id(caller.id)
        if existing:
            raise ConflictException(
                message="A therapist profile already exists for this account",
                code=ErrorCode.THERAPIST_ALREADY_EXISTS,
            )

        display_name = req.display_name or f"{req.first_name} {req.last_name}"
        now = utc_now()

        therapist = TherapistInDB(
            id=str(uuid.uuid4()),
            user_id=caller.id,
            first_name=req.first_name.strip(),
            last_name=req.last_name.strip(),
            display_name=display_name.strip(),
            bio=req.bio.strip(),
            profile_image_url=req.profile_image_url,
            introduction_audio_url=req.introduction_audio_url,
            designation=req.designation.strip(),
            specialization=req.specialization,
            qualifications=req.qualifications,
            experience_years=req.experience_years,
            therapy_hours=req.therapy_hours,
            languages=req.languages,
            expertises=req.expertises,
            session_modes=req.session_modes,
            pricing=PricingModel(
                amount=req.pricing.amount,
                currency=req.pricing.currency,
                duration_minutes=req.pricing.duration_minutes,
            ),
            verification=VerificationModel(status=TherapistVerificationStatus.PENDING),
            status=TherapistStatus.PENDING_VERIFICATION,
            created_at=now,
            updated_at=now,
        )

        await self.therapist_repo.create(therapist)

        # Ensure user has THERAPIST role
        if UserRole.THERAPIST not in caller.roles:
            updated_roles = list(caller.roles) + [UserRole.THERAPIST]
            await self.user_repo.update(caller.id, {"roles": updated_roles})

        return TherapistDetailResponse.from_therapist_db(therapist)

    async def update_therapist(
        self,
        therapist_id: str,
        caller: UserInDB,
        req: UpdateTherapistRequest,
    ) -> TherapistDetailResponse:
        """Update therapist profile with ownership verification and status rules."""
        therapist = await self.therapist_repo.get_by_id(therapist_id)
        if not therapist:
            raise NotFoundException(
                message="Therapist not found",
                code=ErrorCode.THERAPIST_NOT_FOUND,
            )

        is_owner = caller.id == therapist.user_id
        is_admin = any(r in caller.roles for r in [UserRole.ADMIN, UserRole.SUPER_ADMIN])

        if not is_owner and not is_admin:
            raise ForbiddenException(
                message="You do not have permission to modify this therapist profile",
                code=ErrorCode.THERAPIST_ACCESS_DENIED,
            )

        updates: dict[str, Any] = req.model_dump(exclude_unset=True)

        # Validate status change if requested
        if req.status is not None and req.status != therapist.status:
            allowed_transitions = VALID_STATUS_TRANSITIONS.get(therapist.status, set())
            if req.status not in allowed_transitions:
                raise BadRequestException(
                    message=f"Cannot transition status from {therapist.status} to {req.status}",
                    code=ErrorCode.INVALID_STATUS_TRANSITION,
                )

            # Non-admin cannot activate an unverified therapist
            if (
                req.status == TherapistStatus.ACTIVE
                and therapist.verification.status != TherapistVerificationStatus.VERIFIED
                and not is_admin
            ):
                raise BadRequestException(
                    message="Profile must be verified by administration before it can be activated",
                    code=ErrorCode.INVALID_VERIFICATION_STATUS,
                )

        if not updates:
            return TherapistDetailResponse.from_therapist_db(therapist)

        updated_doc = await self.therapist_repo.update(therapist_id, updates)
        if not updated_doc:
            raise NotFoundException(
                message="Therapist not found after update",
                code=ErrorCode.THERAPIST_NOT_FOUND,
            )
        return TherapistDetailResponse.from_therapist_db(updated_doc)

    async def update_verification(
        self,
        therapist_id: str,
        admin_user: UserInDB,
        req: AdminUpdateTherapistVerificationRequest,
    ) -> TherapistDetailResponse:
        """Privileged administrative verification update."""
        therapist = await self.therapist_repo.get_by_id(therapist_id)
        if not therapist:
            raise NotFoundException(
                message="Therapist not found",
                code=ErrorCode.THERAPIST_NOT_FOUND,
            )

        now = utc_now()
        verification_data = {
            "status": req.status,
            "verified_at": now if req.status == TherapistVerificationStatus.VERIFIED else None,
            "verified_by": admin_user.id,
            "rejection_reason": req.rejection_reason
            if req.status == TherapistVerificationStatus.REJECTED
            else None,
        }

        updates: dict[str, Any] = {"verification": verification_data}

        # Auto-activate when verified from PENDING_VERIFICATION
        if (
            req.status == TherapistVerificationStatus.VERIFIED
            and therapist.status == TherapistStatus.PENDING_VERIFICATION
        ):
            updates["status"] = TherapistStatus.ACTIVE

        updated_doc = await self.therapist_repo.update(therapist_id, updates)
        if not updated_doc:
            raise NotFoundException(
                message="Therapist not found",
                code=ErrorCode.THERAPIST_NOT_FOUND,
            )
        return TherapistDetailResponse.from_therapist_db(updated_doc)
