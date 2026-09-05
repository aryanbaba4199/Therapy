"""FastAPI router for Availability and Slot discovery/management endpoints."""

from datetime import date

from fastapi import APIRouter, Depends, Path, Query

from app.common.responses.api_response import ApiResponse
from app.modules.auth.auth_dependency import get_current_active_user
from app.modules.availability.availability_controller import AvailabilityController
from app.modules.availability.availability_dependency import get_availability_service
from app.modules.availability.availability_schema import (
    CreateDateExceptionRequest,
    CreateExtraSlotRequest,
    DateExceptionResponse,
    ExtraSlotResponse,
    GeneratedSlotResponse,
    SetWeeklyScheduleRequest,
    TherapistAvailabilityResponse,
    WeeklyScheduleResponse,
)
from app.modules.availability.availability_service import AvailabilityService
from app.modules.therapist.therapist_constants import SessionMode
from app.modules.therapist.therapist_dependency import get_optional_current_user
from app.modules.user.user_model import UserInDB

router = APIRouter(prefix="/therapists/{therapist_id}", tags=["Availability"])


def get_availability_controller(
    service: AvailabilityService = Depends(get_availability_service),
) -> AvailabilityController:
    """Dependency injecting configured AvailabilityController."""
    return AvailabilityController(service=service)


# ---------------------------------------------------------------------------
# Public Slot Discovery Endpoint
# ---------------------------------------------------------------------------
@router.get(
    "/slots",
    response_model=ApiResponse[list[GeneratedSlotResponse]],
    summary="Discover available consultation slots for a therapist",
)
async def get_available_slots(
    therapist_id: str = Path(..., description="Therapist UUID"),
    date: str | None = Query(default=None, description="Specific date (YYYY-MM-DD)"),
    start_date: str | None = Query(default=None, description="Range start date (YYYY-MM-DD)"),
    end_date: str | None = Query(default=None, description="Range end date (YYYY-MM-DD)"),
    session_mode: SessionMode | None = Query(default=None, description="Consultation delivery mode"),
    current_user: UserInDB | None = Depends(get_optional_current_user),
    controller: AvailabilityController = Depends(get_availability_controller),
) -> ApiResponse[list[GeneratedSlotResponse]]:
    """Retrieve available slots filtered by date and session mode."""
    return await controller.get_available_slots(
        therapist_id=therapist_id,
        target_date=date,
        start_date=start_date,
        end_date=end_date,
        session_mode=session_mode,
        caller=current_user,
    )


# ---------------------------------------------------------------------------
# Therapist Availability (Weekly Schedule & Exceptions) Endpoints
# ---------------------------------------------------------------------------
@router.get(
    "/availability",
    response_model=ApiResponse[TherapistAvailabilityResponse],
    summary="Get therapist weekly working schedule and exceptions",
)
async def get_therapist_availability(
    therapist_id: str = Path(..., description="Therapist UUID"),
    controller: AvailabilityController = Depends(get_availability_controller),
) -> ApiResponse[TherapistAvailabilityResponse]:
    """Retrieve weekly recurring schedule and upcoming exceptions."""
    return await controller.get_availability(therapist_id=therapist_id)


@router.post(
    "/availability",
    response_model=ApiResponse[WeeklyScheduleResponse],
    summary="Set or replace weekly recurring working schedule",
)
async def set_weekly_schedule(
    req: SetWeeklyScheduleRequest,
    therapist_id: str = Path(..., description="Therapist UUID"),
    current_user: UserInDB = Depends(get_current_active_user),
    controller: AvailabilityController = Depends(get_availability_controller),
) -> ApiResponse[WeeklyScheduleResponse]:
    """Configure weekly recurring working hours."""
    return await controller.set_weekly_schedule(
        therapist_id=therapist_id,
        caller=current_user,
        req=req,
    )


@router.delete(
    "/availability",
    response_model=ApiResponse[dict[str, bool]],
    summary="Clear weekly recurring schedule",
)
async def delete_weekly_schedule(
    therapist_id: str = Path(..., description="Therapist UUID"),
    current_user: UserInDB = Depends(get_current_active_user),
    controller: AvailabilityController = Depends(get_availability_controller),
) -> ApiResponse[dict[str, bool]]:
    """Clear all weekly recurring schedule entries."""
    return await controller.delete_weekly_schedule(
        therapist_id=therapist_id,
        caller=current_user,
    )


@router.post(
    "/availability/exceptions",
    response_model=ApiResponse[DateExceptionResponse],
    summary="Add or update date-specific exception / holiday",
)
async def upsert_date_exception(
    req: CreateDateExceptionRequest,
    therapist_id: str = Path(..., description="Therapist UUID"),
    current_user: UserInDB = Depends(get_current_active_user),
    controller: AvailabilityController = Depends(get_availability_controller),
) -> ApiResponse[DateExceptionResponse]:
    """Add a holiday or custom working intervals for a specific date."""
    return await controller.upsert_date_exception(
        therapist_id=therapist_id,
        caller=current_user,
        req=req,
    )


@router.delete(
    "/availability/exceptions/{date_str}",
    response_model=ApiResponse[dict[str, bool]],
    summary="Delete date-specific exception",
)
async def delete_date_exception(
    therapist_id: str = Path(..., description="Therapist UUID"),
    date_str: str = Path(..., description="Date to remove exception for (YYYY-MM-DD)"),
    current_user: UserInDB = Depends(get_current_active_user),
    controller: AvailabilityController = Depends(get_availability_controller),
) -> ApiResponse[dict[str, bool]]:
    """Remove a date-specific override."""
    return await controller.delete_date_exception(
        therapist_id=therapist_id,
        caller=current_user,
        date_str=date_str,
    )


# ---------------------------------------------------------------------------
# Extra Slot Endpoints
# ---------------------------------------------------------------------------
@router.get(
    "/extra-slots",
    response_model=ApiResponse[list[ExtraSlotResponse]],
    summary="List extra consultation slots in date range",
)
async def list_extra_slots(
    therapist_id: str = Path(..., description="Therapist UUID"),
    start_date: str = Query(default_factory=lambda: date.today().isoformat()),
    end_date: str = Query(
        default_factory=lambda: (date.today().replace(year=date.today().year + 1)).isoformat()
    ),
    current_user: UserInDB = Depends(get_current_active_user),
    controller: AvailabilityController = Depends(get_availability_controller),
) -> ApiResponse[list[ExtraSlotResponse]]:
    """Retrieve extra slots."""
    return await controller.list_extra_slots(
        therapist_id=therapist_id,
        caller=current_user,
        start_date=start_date,
        end_date=end_date,
    )


@router.post(
    "/extra-slots",
    response_model=ApiResponse[ExtraSlotResponse],
    summary="Create an extra consultation slot",
)
async def create_extra_slot(
    req: CreateExtraSlotRequest,
    therapist_id: str = Path(..., description="Therapist UUID"),
    current_user: UserInDB = Depends(get_current_active_user),
    controller: AvailabilityController = Depends(get_availability_controller),
) -> ApiResponse[ExtraSlotResponse]:
    """Add a one-off extra slot."""
    return await controller.create_extra_slot(
        therapist_id=therapist_id,
        caller=current_user,
        req=req,
    )


@router.delete(
    "/extra-slots/{slot_id}",
    response_model=ApiResponse[dict[str, bool]],
    summary="Delete an extra consultation slot",
)
async def delete_extra_slot(
    therapist_id: str = Path(..., description="Therapist UUID"),
    slot_id: str = Path(..., description="Extra slot UUID"),
    current_user: UserInDB = Depends(get_current_active_user),
    controller: AvailabilityController = Depends(get_availability_controller),
) -> ApiResponse[dict[str, bool]]:
    """Remove a one-off extra slot."""
    return await controller.delete_extra_slot(
        therapist_id=therapist_id,
        caller=current_user,
        slot_id=slot_id,
    )
