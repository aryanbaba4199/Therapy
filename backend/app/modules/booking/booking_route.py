"""FastAPI router for Booking and Reservation endpoints."""

from fastapi import APIRouter, Depends, Path, Query

from app.common.pagination.pagination import PaginatedData
from app.common.responses.api_response import ApiResponse
from app.modules.auth.auth_dependency import get_current_active_user
from app.modules.booking.booking_constants import BookingStatus
from app.modules.booking.booking_controller import BookingController
from app.modules.booking.booking_dependency import get_booking_service
from app.modules.booking.booking_schema import (
    BookingDetailResponse,
    BookingSummaryResponse,
    CancelBookingRequest,
    ConfirmBookingRequest,
    CreateReservationRequest,
    ReservationResponse,
)
from app.modules.booking.booking_service import BookingService
from app.modules.user.user_model import UserInDB

router = APIRouter(prefix="/bookings", tags=["Bookings"])


def get_booking_controller(
    service: BookingService = Depends(get_booking_service),
) -> BookingController:
    """Dependency injecting configured BookingController."""
    return BookingController(service=service)


# ---------------------------------------------------------------------------
# Reservation Endpoints
# ---------------------------------------------------------------------------
@router.post(
    "/reservations",
    response_model=ApiResponse[ReservationResponse],
    status_code=201,
    summary="Create temporary slot reservation",
)
async def create_reservation(
    req: CreateReservationRequest,
    current_user: UserInDB = Depends(get_current_active_user),
    controller: BookingController = Depends(get_booking_controller),
) -> ApiResponse[ReservationResponse]:
    """Atomically place a temporary hold on a consultation slot."""
    return await controller.create_reservation(caller=current_user, req=req)


@router.get(
    "/reservations/{reservation_id}",
    response_model=ApiResponse[ReservationResponse],
    summary="Get reservation status and countdown timer",
)
async def get_reservation(
    reservation_id: str = Path(..., description="Reservation UUID"),
    current_user: UserInDB = Depends(get_current_active_user),
    controller: BookingController = Depends(get_booking_controller),
) -> ApiResponse[ReservationResponse]:
    """Retrieve reservation details and remaining seconds."""
    return await controller.get_reservation(caller=current_user, reservation_id=reservation_id)


@router.delete(
    "/reservations/{reservation_id}",
    response_model=ApiResponse[dict[str, bool]],
    summary="Cancel reservation and release slot hold",
)
async def cancel_reservation(
    reservation_id: str = Path(..., description="Reservation UUID"),
    current_user: UserInDB = Depends(get_current_active_user),
    controller: BookingController = Depends(get_booking_controller),
) -> ApiResponse[dict[str, bool]]:
    """Release a held slot."""
    return await controller.cancel_reservation(caller=current_user, reservation_id=reservation_id)


# ---------------------------------------------------------------------------
# Booking Lifecycle Endpoints
# ---------------------------------------------------------------------------
@router.post(
    "/confirm",
    response_model=ApiResponse[BookingDetailResponse],
    status_code=201,
    summary="Confirm booking from active reservation",
)
@router.post(
    "",
    response_model=ApiResponse[BookingDetailResponse],
    status_code=201,
    summary="Confirm booking from active reservation (alias)",
    include_in_schema=False,
)
async def confirm_booking(
    req: ConfirmBookingRequest,
    current_user: UserInDB = Depends(get_current_active_user),
    controller: BookingController = Depends(get_booking_controller),
) -> ApiResponse[BookingDetailResponse]:
    """Convert an active reservation into a confirmed consultation booking."""
    return await controller.confirm_booking(caller=current_user, req=req)


@router.get(
    "",
    response_model=ApiResponse[PaginatedData[BookingSummaryResponse]],
    summary="List authenticated client's consultation bookings",
)
async def list_client_bookings(
    page: int = Query(default=1, ge=1, description="Page number"),
    limit: int = Query(default=10, ge=1, le=50, description="Items per page"),
    status: BookingStatus | None = Query(default=None, description="Filter by booking status"),
    current_user: UserInDB = Depends(get_current_active_user),
    controller: BookingController = Depends(get_booking_controller),
) -> ApiResponse[PaginatedData[BookingSummaryResponse]]:
    """Retrieve paginated consultation history for caller."""
    return await controller.list_client_bookings(
        caller=current_user,
        page=page,
        limit=limit,
        status=status,
    )


@router.get(
    "/{booking_id}",
    response_model=ApiResponse[BookingDetailResponse],
    summary="Get detailed consultation booking information",
)
async def get_booking_detail(
    booking_id: str = Path(..., description="Booking UUID"),
    current_user: UserInDB = Depends(get_current_active_user),
    controller: BookingController = Depends(get_booking_controller),
) -> ApiResponse[BookingDetailResponse]:
    """Retrieve full consultation details and snapshot audit."""
    return await controller.get_booking_detail(caller=current_user, booking_id=booking_id)


@router.post(
    "/{booking_id}/cancel",
    response_model=ApiResponse[BookingDetailResponse],
    summary="Cancel confirmed consultation booking",
)
async def cancel_booking(
    req: CancelBookingRequest,
    booking_id: str = Path(..., description="Booking UUID"),
    current_user: UserInDB = Depends(get_current_active_user),
    controller: BookingController = Depends(get_booking_controller),
) -> ApiResponse[BookingDetailResponse]:
    """Cancel booking if allowed by lifecycle policies."""
    return await controller.cancel_booking(caller=current_user, booking_id=booking_id, req=req)
