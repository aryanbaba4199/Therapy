"""Presentation controller layer for Review endpoints."""

from app.common.responses.api_response import ApiResponse, success_response
from app.modules.review.review_schema import (
    CreateReviewRequest,
    ModerateReviewRequest,
    PublicReviewResponse,
    ReviewResponse,
    TherapistRatingSummaryResponse,
)
from app.modules.review.review_service import ReviewService
from app.modules.user.user_model import UserInDB


class ReviewController:
    """Controller handling response serialization for Review and Rating APIs."""

    def __init__(self, service: ReviewService) -> None:
        self.service = service

    async def create_review(
        self, caller: UserInDB, req: CreateReviewRequest
    ) -> ApiResponse[ReviewResponse]:
        res = await self.service.create_review(caller=caller, req=req)
        return success_response(data=res, message="Review submitted successfully")

    async def get_review_by_id(
        self, caller: UserInDB, review_id: str
    ) -> ApiResponse[ReviewResponse]:
        res = await self.service.get_review_by_id(caller=caller, review_id=review_id)
        return success_response(data=res)

    async def list_therapist_reviews(
        self, therapist_id: str, page: int, limit: int
    ) -> ApiResponse[list[PublicReviewResponse]]:
        items, total = await self.service.list_therapist_reviews(
            therapist_id=therapist_id, page=page, limit=limit
        )
        return success_response(
            data=items,
            meta={
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit if total > 0 else 0,
            },
        )

    async def get_therapist_rating_summary(
        self, therapist_id: str
    ) -> ApiResponse[TherapistRatingSummaryResponse]:
        res = await self.service.get_therapist_rating_summary(therapist_id=therapist_id)
        return success_response(data=res)

    async def list_client_reviews(
        self, caller: UserInDB, page: int, limit: int
    ) -> ApiResponse[list[ReviewResponse]]:
        items, total = await self.service.list_client_reviews(
            caller=caller, page=page, limit=limit
        )
        return success_response(
            data=items,
            meta={
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit if total > 0 else 0,
            },
        )

    async def moderate_review(
        self, review_id: str, req: ModerateReviewRequest
    ) -> ApiResponse[ReviewResponse]:
        res = await self.service.moderate_review(
            review_id=review_id, status=req.status
        )
        return success_response(data=res, message="Review status updated successfully")
