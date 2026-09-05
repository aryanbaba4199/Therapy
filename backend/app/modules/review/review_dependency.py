"""Dependency injection providers for Review module."""

from typing import Any

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.database.mongodb import get_database
from app.modules.review.review_repository import ReviewRepository
from app.modules.review.review_service import ReviewService
from app.modules.session.session_dependency import get_session_repository
from app.modules.session.session_repository import SessionRepository


def get_review_repository(
    db: AsyncIOMotorDatabase[dict[str, Any]] = Depends(get_database),
) -> ReviewRepository:
    return ReviewRepository(db=db)


def get_review_service(
    db: AsyncIOMotorDatabase[dict[str, Any]] = Depends(get_database),
    review_repo: ReviewRepository = Depends(get_review_repository),
    session_repo: SessionRepository = Depends(get_session_repository),
) -> ReviewService:
    return ReviewService(
        db=db,
        review_repo=review_repo,
        session_repo=session_repo,
    )
