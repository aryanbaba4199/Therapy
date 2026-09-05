"""FastAPI route registration for Review and Feedback endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.common.responses.api_response import ApiResponse
from app.modules.auth.auth_dependency import get_current_active_user, require_roles
from app.modules.review.review_controller import ReviewController
from app.modules.review.review_dependency import get_review_service
from app.modules.review.review_schema import (
    CreateReviewRequest,
    ModerateReviewRequest,
    PublicReviewResponse,
    ReviewResponse,
    TherapistRatingSummaryResponse,
)
from app.modules.review.review_service import ReviewService
from app.modules.user.user_constants import UserRole
from app.modules.user.user_model import UserInDB

router = APIRouter(prefix="/reviews", tags=["Reviews & Feedback"])


def get_review_controller(
    service: ReviewService = Depends(get_review_service),
) -> ReviewController:
    return ReviewController(service=service)


@router.post(
    "",
    response_model=ApiResponse[ReviewResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Submit review for completed therapy session",
)
async def create_review(
    req: CreateReviewRequest,
    caller: Annotated[UserInDB, Depends(get_current_active_user)],
    controller: Annotated[ReviewController, Depends(get_review_controller)],
) -> ApiResponse[ReviewResponse]:
    return await controller.create_review(caller=caller, req=req)


@router.get(
    "/my/history",
    response_model=ApiResponse[list[ReviewResponse]],
    summary="List reviews submitted by current client",
)
async def list_my_reviews(
    caller: Annotated[UserInDB, Depends(get_current_active_user)],
    controller: Annotated[ReviewController, Depends(get_review_controller)],
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
) -> ApiResponse[list[ReviewResponse]]:
    return await controller.list_client_reviews(caller=caller, page=page, limit=limit)


@router.get(
    "/therapist/{therapist_id}",
    response_model=ApiResponse[list[PublicReviewResponse]],
    summary="List public reviews for a therapist",
)
async def list_therapist_reviews(
    therapist_id: str,
    controller: Annotated[ReviewController, Depends(get_review_controller)],
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
) -> ApiResponse[list[PublicReviewResponse]]:
    return await controller.list_therapist_reviews(
        therapist_id=therapist_id, page=page, limit=limit
    )


@router.get(
    "/therapist/{therapist_id}/summary",
    response_model=ApiResponse[TherapistRatingSummaryResponse],
    summary="Get aggregated rating metrics for a therapist",
)
async def get_therapist_rating_summary(
    therapist_id: str,
    controller: Annotated[ReviewController, Depends(get_review_controller)],
) -> ApiResponse[TherapistRatingSummaryResponse]:
    return await controller.get_therapist_rating_summary(therapist_id=therapist_id)


@router.get(
    "/{review_id}",
    response_model=ApiResponse[ReviewResponse],
    summary="Get review details",
)
async def get_review_by_id(
    review_id: str,
    caller: Annotated[UserInDB, Depends(get_current_active_user)],
    controller: Annotated[ReviewController, Depends(get_review_controller)],
) -> ApiResponse[ReviewResponse]:
    return await controller.get_review_by_id(caller=caller, review_id=review_id)


@router.patch(
    "/{review_id}/moderate",
    response_model=ApiResponse[ReviewResponse],
    summary="Moderate review publication status (Staff/Admin only)",
)
async def moderate_review(
    review_id: str,
    req: ModerateReviewRequest,
    caller: Annotated[
        UserInDB,
        Depends(
            require_roles(
                UserRole.STAFF, UserRole.ADMIN, UserRole.SUPER_ADMIN
            )
        ),
    ],
    controller: Annotated[ReviewController, Depends(get_review_controller)],
) -> ApiResponse[ReviewResponse]:
    return await controller.moderate_review(review_id=review_id, req=req)
