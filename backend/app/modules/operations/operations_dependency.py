"""Dependencies for Operations, Admin, and First Responder module."""

from collections.abc import Callable
from typing import Annotated, Any

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.common.exceptions.app_exceptions import ForbiddenException
from app.common.exceptions.error_codes import ErrorCode
from app.database.mongodb import get_database
from app.modules.auth.auth_dependency import get_current_active_user
from app.modules.booking.booking_dependency import get_booking_repository
from app.modules.booking.booking_repository import BookingRepository
from app.modules.operations.operations_constants import Permission
from app.modules.operations.operations_repository import OperationsRepository
from app.modules.operations.operations_service import OperationsService
from app.modules.payment.payment_dependency import get_payment_repository
from app.modules.payment.payment_repository import PaymentRepository
from app.modules.therapist.therapist_dependency import (
    get_therapist_repository,
    get_therapist_service,
)
from app.modules.therapist.therapist_repository import TherapistRepository
from app.modules.therapist.therapist_service import TherapistService
from app.modules.user.user_dependency import get_user_repository
from app.modules.user.user_model import UserInDB
from app.modules.user.user_repository import UserRepository


def get_operations_repository(
    db: Annotated[AsyncIOMotorDatabase[dict[str, Any]], Depends(get_database)],
) -> OperationsRepository:
    """Provide OperationsRepository instance."""
    return OperationsRepository(db)


def get_operations_service(
    db: Annotated[AsyncIOMotorDatabase[dict[str, Any]], Depends(get_database)],
    ops_repo: Annotated[OperationsRepository, Depends(get_operations_repository)],
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
    therapist_repo: Annotated[TherapistRepository, Depends(get_therapist_repository)],
    therapist_service: Annotated[TherapistService, Depends(get_therapist_service)],
    booking_repo: Annotated[BookingRepository, Depends(get_booking_repository)],
    payment_repo: Annotated[PaymentRepository, Depends(get_payment_repository)],
) -> OperationsService:
    """Provide OperationsService instance."""
    return OperationsService(
        db=db,
        ops_repo=ops_repo,
        user_repo=user_repo,
        therapist_repo=therapist_repo,
        therapist_service=therapist_service,
        booking_repo=booking_repo,
        payment_repo=payment_repo,
    )


def require_permission(*permissions: Permission) -> Callable[..., Any]:
    """Dependency factory enforcing that the authenticated caller has required permissions."""

    async def permission_checker(
        current_user: Annotated[UserInDB, Depends(get_current_active_user)],
        ops_service: Annotated[OperationsService, Depends(get_operations_service)],
    ) -> UserInDB:
        for perm in permissions:
            if not ops_service.has_permission(current_user, perm):
                raise ForbiddenException(
                    message=f"Access denied: Missing required permission '{perm.value}'",
                    code=ErrorCode.OPS_PERMISSION_REQUIRED,
                )
        return current_user

    return permission_checker
