"""Presentation controller layer for Availability endpoints."""

from app.common.responses.api_response import ApiResponse, success_response
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
from app.modules.user.user_model import UserInDB


class AvailabilityController:
    """Controller handling HTTP requests and formatting ApiResponse envelopes."""

    def __init__(self, service: AvailabilityService) -> None:
        self.service = service

    async def get_availability(
        self, therapist_id: str
    ) -> ApiResponse[TherapistAvailabilityResponse]:
        """Get therapist weekly schedule and upcoming exceptions."""
        result = await self.service.get_therapist_availability(therapist_id)
        return success_response(data=result, message="Therapist availability retrieved successfully")

    async def set_weekly_schedule(
        self,
        therapist_id: str,
        caller: UserInDB,
        req: SetWeeklyScheduleRequest,
    ) -> ApiResponse[WeeklyScheduleResponse]:
        """Set recurring weekly schedule."""
        result = await self.service.set_weekly_schedule(therapist_id, caller, req)
        return success_response(data=result, message="Weekly schedule saved successfully")

    async def delete_weekly_schedule(
        self, therapist_id: str, caller: UserInDB
    ) -> ApiResponse[dict[str, bool]]:
        """Clear weekly schedule."""
        await self.service.delete_weekly_schedule(therapist_id, caller)
        return success_response(data={"deleted": True}, message="Weekly schedule cleared successfully")

    async def upsert_date_exception(
        self,
        therapist_id: str,
        caller: UserInDB,
        req: CreateDateExceptionRequest,
    ) -> ApiResponse[DateExceptionResponse]:
        """Set date exception or holiday."""
        result = await self.service.upsert_date_exception(therapist_id, caller, req)
        return success_response(data=result, message="Date exception saved successfully")

    async def delete_date_exception(
        self, therapist_id: str, caller: UserInDB, date_str: str
    ) -> ApiResponse[dict[str, bool]]:
        """Remove date exception."""
        await self.service.delete_date_exception(therapist_id, caller, date_str)
        return success_response(data={"deleted": True}, message="Date exception removed successfully")

    async def list_extra_slots(
        self,
        therapist_id: str,
        caller: UserInDB,
        start_date: str,
        end_date: str,
    ) -> ApiResponse[list[ExtraSlotResponse]]:
        """List extra slots in date range."""
        slots = await self.service.list_extra_slots(therapist_id, caller, start_date, end_date)
        return success_response(data=slots, message="Extra slots retrieved successfully")

    async def create_extra_slot(
        self,
        therapist_id: str,
        caller: UserInDB,
        req: CreateExtraSlotRequest,
    ) -> ApiResponse[ExtraSlotResponse]:
        """Create new extra slot."""
        slot = await self.service.create_extra_slot(therapist_id, caller, req)
        return success_response(data=slot, message="Extra slot created successfully")

    async def delete_extra_slot(
        self, therapist_id: str, caller: UserInDB, slot_id: str
    ) -> ApiResponse[dict[str, bool]]:
        """Remove extra slot."""
        await self.service.delete_extra_slot(therapist_id, caller, slot_id)
        return success_response(data={"deleted": True}, message="Extra slot removed successfully")

    async def get_available_slots(
        self,
        therapist_id: str,
        target_date: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        session_mode: SessionMode | None = None,
        caller: UserInDB | None = None,
    ) -> ApiResponse[list[GeneratedSlotResponse]]:
        """Public slot discovery."""
        slots = await self.service.get_available_slots(
            therapist_id=therapist_id,
            target_date=target_date,
            start_date=start_date,
            end_date=end_date,
            session_mode=session_mode,
            caller=caller,
        )
        return success_response(data=slots, message="Available slots retrieved successfully")
