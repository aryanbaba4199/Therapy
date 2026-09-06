"""Service layer orchestrating review lifecycle, eligibility, privacy, and ratings."""

import uuid
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

from app.common.exceptions.app_exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.common.exceptions.error_codes import ErrorCode
from app.common.utils.datetime_utils import utc_now
from app.modules.review.review_constants import ReviewStatus
from app.modules.review.review_model import ReviewInDB
from app.modules.review.review_repository import ReviewRepository
from app.modules.review.review_schema import (
    CreateReviewRequest,
    PublicReviewResponse,
    ReviewResponse,
    TherapistRatingSummaryResponse,
)
from app.modules.session.session_constants import SessionStatus
from app.modules.session.session_repository import SessionRepository
from app.modules.therapist.therapist_repository import TherapistRepository
from app.modules.user.user_constants import UserRole
from app.modules.user.user_model import UserInDB


class ReviewService:
    """Core domain service for review submission, eligibility, and aggregation."""

    def __init__(
        self,
        db: AsyncIOMotorDatabase[dict[str, Any]],
        review_repo: ReviewRepository | None = None,
        session_repo: SessionRepository | None = None,
        therapist_repo: TherapistRepository | None = None,
    ) -> None:
        self.db = db
        self.review_repo = review_repo or ReviewRepository(db)
        self.session_repo = session_repo or SessionRepository(db)
        self.therapist_repo = therapist_repo or TherapistRepository(db)

    def _generate_safe_display_name(self, caller: UserInDB, is_anonymous: bool) -> str:
        """Construct a privacy-safe display name that never exposes contact info."""
        if is_anonymous:
            return "Anonymous Client"
        first = (caller.first_name or "").strip()
        last = (caller.last_name or "").strip()
        if first and last:
            return f"{first} {last[0]}."
        if first:
            return first
        return "Verified Client"

    async def create_review(
        self, caller: UserInDB, req: CreateReviewRequest
    ) -> ReviewResponse:
        """Submit a review for an eligible completed therapy session."""
        # 1. Rating bounds validation
        if req.rating < 1 or req.rating > 5:
            raise BadRequestException(
                message="Rating must be an integer between 1 and 5 stars.",
                code=ErrorCode.REVIEW_INVALID_RATING,
            )

        # 2. Verify session exists
        session = await self.session_repo.get_session_by_id(req.session_id)
        if not session:
            raise NotFoundException(
                message=f"Session '{req.session_id}' not found.",
                code=ErrorCode.SESSION_NOT_FOUND,
            )

        # 3. Ownership / IDOR validation: Only the client who booked can review
        if session.client_id != caller.id:
            raise ForbiddenException(
                message="You can only submit a review for your own therapy session.",
                code=ErrorCode.REVIEW_FORBIDDEN,
            )

        # 4. Lifecycle eligibility: Session MUST be COMPLETED
        if session.status != SessionStatus.COMPLETED:
            raise BadRequestException(
                message="Only completed therapy sessions are eligible for a review.",
                code=ErrorCode.REVIEW_NOT_ELIGIBLE,
            )

        # 5. One review per session invariant check
        existing = await self.review_repo.get_by_session_id(session.id)
        if existing:
            raise ConflictException(
                message="A review has already been submitted for this session.",
                code=ErrorCode.REVIEW_ALREADY_EXISTS,
            )

        # 6. Build model with sanitized display name
        display_name = self._generate_safe_display_name(caller, req.is_anonymous)
        now = utc_now()
        review = ReviewInDB(
            id=str(uuid.uuid4()),
            session_id=session.id,
            booking_id=session.booking_id,
            therapist_id=session.therapist_id,
            client_id=caller.id,
            rating=req.rating,
            comment=(req.comment or "").strip(),
            client_display_name=display_name,
            is_anonymous=req.is_anonymous,
            status=ReviewStatus.PUBLISHED,
            created_at=now,
            updated_at=now,
        )

        try:
            saved = await self.review_repo.create(review)
            return ReviewResponse.from_db(saved)
        except DuplicateKeyError:
            # Caught if concurrent requests simultaneously pass the check
            raise ConflictException(
                message="A review has already been submitted for this session.",
                code=ErrorCode.REVIEW_ALREADY_EXISTS,
            ) from None

    async def get_review_by_id(
        self, caller: UserInDB, review_id: str
    ) -> ReviewResponse:
        """Fetch review by ID with visibility checks."""
        review = await self.review_repo.get_by_id(review_id)
        if not review:
            raise NotFoundException(
                message=f"Review '{review_id}' not found.",
                code=ErrorCode.REVIEW_NOT_FOUND,
            )

        is_staff = any(
            role in [UserRole.STAFF, UserRole.ADMIN, UserRole.SUPER_ADMIN]
            for role in caller.roles
        )
        is_owner = review.client_id == caller.id
        is_therapist = False
        therapist = await self.therapist_repo.get_by_id(review.therapist_id)
        if therapist and therapist.user_id == caller.id:
            is_therapist = True

        if not is_owner and not is_staff and not is_therapist:
            raise ForbiddenException(
                message="You do not have permission to view this review's internal details",
                code=ErrorCode.FORBIDDEN,
            )

        if review.status == ReviewStatus.HIDDEN and not is_staff and not is_owner:
            raise NotFoundException(
                message="This review is hidden.",
                code=ErrorCode.REVIEW_HIDDEN,
            )

        return ReviewResponse.from_db(review)

    async def list_therapist_reviews(
        self, therapist_id: str, page: int = 1, limit: int = 20
    ) -> tuple[list[PublicReviewResponse], int]:
        """Public list of published reviews for a therapist profile."""
        reviews, total = await self.review_repo.list_for_therapist(
            therapist_id=therapist_id,
            status=ReviewStatus.PUBLISHED,
            page=page,
            limit=limit,
        )
        return [PublicReviewResponse.from_db(r) for r in reviews], total

    async def get_therapist_rating_summary(
        self, therapist_id: str
    ) -> TherapistRatingSummaryResponse:
        """Get aggregate rating and star distribution for a therapist."""
        return await self.review_repo.get_therapist_rating_summary(therapist_id)

    async def list_client_reviews(
        self, caller: UserInDB, page: int = 1, limit: int = 20
    ) -> tuple[list[ReviewResponse], int]:
        """List reviews authored by current authenticated client."""
        reviews, total = await self.review_repo.list_for_client(
            client_id=caller.id, page=page, limit=limit
        )
        return [ReviewResponse.from_db(r) for r in reviews], total

    async def moderate_review(
        self, review_id: str, status: ReviewStatus
    ) -> ReviewResponse:
        """Update review moderation status (Staff/Admin only)."""
        review = await self.review_repo.update_status(review_id, status)
        if not review:
            raise NotFoundException(
                message=f"Review '{review_id}' not found.",
                code=ErrorCode.REVIEW_NOT_FOUND,
            )
        return ReviewResponse.from_db(review)
