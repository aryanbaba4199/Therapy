"""Presentation controller layer for Booking and Reservation endpoints."""

from app.common.pagination.pagination import PaginatedData, PaginationParams
from app.common.responses.api_response import ApiResponse, success_response
from app.modules.booking.booking_constants import BookingStatus
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


class BookingController:
    """Controller handling HTTP serialization and response envelopes for bookings."""

    def __init__(self, service: BookingService) -> None:
        self.service = service

    async def create_reservation(
        self, caller: UserInDB, req: CreateReservationRequest
    ) -> ApiResponse[ReservationResponse]:
        """Hold a slot temporarily."""
        result = await self.service.create_reservation(caller, req)
        return success_response(
            data=result,
            message="Slot temporarily reserved. Please confirm within the countdown window.",
        )

    async def get_reservation(
        self, caller: UserInDB, reservation_id: str
    ) -> ApiResponse[ReservationResponse]:
        """Fetch reservation details and active countdown."""
        result = await self.service.get_reservation(caller, reservation_id)
        return success_response(
            data=result,
            message="Reservation details retrieved successfully",
        )

    async def cancel_reservation(
        self, caller: UserInDB, reservation_id: str
    ) -> ApiResponse[dict[str, bool]]:
        """Cancel and release reservation."""
        await self.service.cancel_reservation(caller, reservation_id)
        return success_response(
            data={"cancelled": True},
            message="Reservation cancelled and slot released successfully",
        )

    async def confirm_booking(
        self, caller: UserInDB, req: ConfirmBookingRequest
    ) -> ApiResponse[BookingDetailResponse]:
        """Confirm booking from reservation."""
        result = await self.service.confirm_booking(caller, req)
        return success_response(
            data=result,
            message="Consultation booking confirmed successfully",
        )

    async def list_client_bookings(
        self,
        caller: UserInDB,
        page: int,
        limit: int,
        status: BookingStatus | None,
    ) -> ApiResponse[PaginatedData[BookingSummaryResponse]]:
        """List paginated bookings for client."""
        pagination = PaginationParams(page=page, limit=limit)
        status_filter = [status] if status else None
        result = await self.service.list_client_bookings(
            caller=caller,
            pagination=pagination,
            status_filter=status_filter,
        )
        return success_response(
            data=result,
            message="Bookings retrieved successfully",
        )

    async def get_booking_detail(
        self, caller: UserInDB, booking_id: str
    ) -> ApiResponse[BookingDetailResponse]:
        """Retrieve booking detail."""
        result = await self.service.get_booking_detail(caller, booking_id)
        return success_response(
            data=result,
            message="Booking details retrieved successfully",
        )

    async def cancel_booking(
        self, caller: UserInDB, booking_id: str, req: CancelBookingRequest
    ) -> ApiResponse[BookingDetailResponse]:
        """Cancel an existing booking."""
        result = await self.service.cancel_booking(caller, booking_id, req)
        return success_response(
            data=result,
            message="Booking cancelled successfully",
        )
