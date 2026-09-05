"""Business logic and workflow coordination for Therapist Availability and Slot Generation."""

import uuid
from datetime import date, timedelta

from app.common.exceptions.app_exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.common.exceptions.error_codes import ErrorCode
from app.common.utils.datetime_utils import utc_now
from app.modules.availability.availability_constants import (
    DEFAULT_TIMEZONE,
    MAX_SLOT_DISCOVERY_DAYS,
    DayOfWeek,
    SlotStatus,
)
from app.modules.availability.availability_model import (
    DateExceptionInDB,
    DayInterval,
    DaySchedule,
    ExtraSlotInDB,
    WeeklyScheduleInDB,
)
from app.modules.availability.availability_repository import AvailabilityRepository
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
from app.modules.availability.slot_engine import generate_slots_for_date
from app.modules.therapist.therapist_constants import (
    SessionMode,
    TherapistStatus,
    TherapistVerificationStatus,
)
from app.modules.therapist.therapist_model import TherapistInDB
from app.modules.therapist.therapist_repository import TherapistRepository
from app.modules.user.user_constants import UserRole
from app.modules.user.user_model import UserInDB


class AvailabilityService:
    """Domain service managing schedules, exceptions, extra slots, and slot generation."""

    def __init__(
        self,
        availability_repo: AvailabilityRepository,
        therapist_repo: TherapistRepository,
    ) -> None:
        self.availability_repo = availability_repo
        self.therapist_repo = therapist_repo

    async def _get_therapist_or_raise(self, therapist_id: str) -> TherapistInDB:
        """Retrieve therapist or raise 404."""
        therapist = await self.therapist_repo.get_by_id(therapist_id)
        if not therapist:
            raise NotFoundException(
                message=f"Therapist with ID '{therapist_id}' not found",
                code=ErrorCode.THERAPIST_NOT_FOUND,
            )
        return therapist

    def _verify_ownership_or_admin(self, caller: UserInDB, therapist: TherapistInDB) -> None:
        """Verify that caller owns the therapist profile or holds elevated staff/admin roles."""
        is_owner = caller.id == therapist.user_id
        is_admin = any(
            r in caller.roles
            for r in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.STAFF]
        )
        if not is_owner and not is_admin:
            raise ForbiddenException(
                message="You do not have permission to manage this therapist's availability",
                code=ErrorCode.THERAPIST_ACCESS_DENIED,
            )

    async def get_therapist_availability(
        self, therapist_id: str
    ) -> TherapistAvailabilityResponse:
        """Retrieve weekly schedule and active upcoming exceptions."""
        therapist = await self._get_therapist_or_raise(therapist_id)
        schedule = await self.availability_repo.get_weekly_schedule(therapist_id)

        today_str = date.today().isoformat()
        future_str = (date.today() + timedelta(days=60)).isoformat()
        exceptions = await self.availability_repo.get_exceptions_for_range(
            therapist_id, today_str, future_str
        )

        schedule_resp = WeeklyScheduleResponse.from_db(schedule) if schedule else None
        exception_resps = [DateExceptionResponse.from_db(e) for e in exceptions]

        return TherapistAvailabilityResponse(
            therapist_id=therapist.id,
            timezone=schedule.timezone if schedule else DEFAULT_TIMEZONE,
            schedule=schedule_resp,
            exceptions=exception_resps,
        )

    async def set_weekly_schedule(
        self,
        therapist_id: str,
        caller: UserInDB,
        req: SetWeeklyScheduleRequest,
    ) -> WeeklyScheduleResponse:
        """Create or update a therapist's weekly recurring schedule."""
        therapist = await self._get_therapist_or_raise(therapist_id)
        self._verify_ownership_or_admin(caller, therapist)

        days_in_db: list[DaySchedule] = []
        for day_req in req.days:
            intervals_in_db = [
                DayInterval(
                    start_time=i.start_time,
                    end_time=i.end_time,
                    session_modes=i.session_modes,
                )
                for i in day_req.intervals
            ]
            days_in_db.append(
                DaySchedule(
                    day_of_week=day_req.day_of_week,
                    intervals=intervals_in_db,
                )
            )

        existing = await self.availability_repo.get_weekly_schedule(therapist_id)
        schedule_doc = WeeklyScheduleInDB(
            id=existing.id if existing else str(uuid.uuid4()),
            therapist_id=therapist_id,
            timezone=req.timezone,
            days=days_in_db,
            created_at=existing.created_at if existing else utc_now(),
            updated_at=utc_now(),
        )

        saved = await self.availability_repo.upsert_weekly_schedule(schedule_doc)
        return WeeklyScheduleResponse.from_db(saved)

    async def delete_weekly_schedule(self, therapist_id: str, caller: UserInDB) -> bool:
        """Clear weekly schedule for a therapist."""
        therapist = await self._get_therapist_or_raise(therapist_id)
        self._verify_ownership_or_admin(caller, therapist)
        return await self.availability_repo.delete_weekly_schedule(therapist_id)

    async def upsert_date_exception(
        self,
        therapist_id: str,
        caller: UserInDB,
        req: CreateDateExceptionRequest,
    ) -> DateExceptionResponse:
        """Create or update a date-specific override or unavailable holiday."""
        therapist = await self._get_therapist_or_raise(therapist_id)
        self._verify_ownership_or_admin(caller, therapist)

        existing = await self.availability_repo.get_exception(therapist_id, req.date)
        custom_intervals = [
            DayInterval(
                start_time=i.start_time,
                end_time=i.end_time,
                session_modes=i.session_modes,
            )
            for i in req.custom_intervals
        ]

        exception_doc = DateExceptionInDB(
            id=existing.id if existing else str(uuid.uuid4()),
            therapist_id=therapist_id,
            date=req.date,
            is_unavailable=req.is_unavailable,
            custom_intervals=custom_intervals,
            reason=req.reason,
            created_at=existing.created_at if existing else utc_now(),
            updated_at=utc_now(),
        )

        saved = await self.availability_repo.upsert_exception(exception_doc)
        return DateExceptionResponse.from_db(saved)

    async def delete_date_exception(
        self, therapist_id: str, caller: UserInDB, date_str: str
    ) -> bool:
        """Delete date exception."""
        therapist = await self._get_therapist_or_raise(therapist_id)
        self._verify_ownership_or_admin(caller, therapist)
        deleted = await self.availability_repo.delete_exception(therapist_id, date_str)
        if not deleted:
            raise NotFoundException(
                message=f"Date exception for date '{date_str}' not found",
                code=ErrorCode.DATE_EXCEPTION_NOT_FOUND,
            )
        return True

    async def list_extra_slots(
        self,
        therapist_id: str,
        caller: UserInDB,
        start_date: str,
        end_date: str,
    ) -> list[ExtraSlotResponse]:
        """List extra slots for a therapist within a date range."""
        therapist = await self._get_therapist_or_raise(therapist_id)
        self._verify_ownership_or_admin(caller, therapist)
        slots = await self.availability_repo.get_extra_slots_for_range(
            therapist_id, start_date, end_date
        )
        return [ExtraSlotResponse.from_db(s) for s in slots]

    async def create_extra_slot(
        self,
        therapist_id: str,
        caller: UserInDB,
        req: CreateExtraSlotRequest,
    ) -> ExtraSlotResponse:
        """Create an extra slot for a therapist."""
        therapist = await self._get_therapist_or_raise(therapist_id)
        self._verify_ownership_or_admin(caller, therapist)

        # Check if date is in the past
        target_d = date.fromisoformat(req.date)
        if target_d < date.today():
            raise BadRequestException(
                message="Cannot add extra slot for a past date",
                code=ErrorCode.DATE_IN_PAST,
            )

        # Check overlap with existing extra slots on same date & mode
        existing_extras = await self.availability_repo.get_extra_slots_for_range(
            therapist_id, req.date, req.date
        )
        for ex in existing_extras:
            if ex.session_mode == req.session_mode and not (
                req.end_time <= ex.start_time or req.start_time >= ex.end_time
            ):
                raise ConflictException(
                    message=f"Extra slot overlaps with an existing extra slot ({ex.start_time} - {ex.end_time})",
                    code=ErrorCode.EXTRA_SLOT_CONFLICT,
                )

        extra_doc = ExtraSlotInDB(
            id=str(uuid.uuid4()),
            therapist_id=therapist_id,
            date=req.date,
            start_time=req.start_time,
            end_time=req.end_time,
            session_mode=req.session_mode,
            status=SlotStatus.AVAILABLE,
            created_at=utc_now(),
            updated_at=utc_now(),
        )

        saved = await self.availability_repo.create_extra_slot(extra_doc)
        return ExtraSlotResponse.from_db(saved)

    async def delete_extra_slot(
        self, therapist_id: str, caller: UserInDB, slot_id: str
    ) -> bool:
        """Remove an extra slot."""
        therapist = await self._get_therapist_or_raise(therapist_id)
        self._verify_ownership_or_admin(caller, therapist)

        slot = await self.availability_repo.get_extra_slot_by_id(slot_id)
        if not slot or slot.therapist_id != therapist_id:
            raise NotFoundException(
                message="Extra slot not found",
                code=ErrorCode.EXTRA_SLOT_NOT_FOUND,
            )

        return await self.availability_repo.delete_extra_slot(slot_id)

    async def get_available_slots(
        self,
        therapist_id: str,
        target_date: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        session_mode: SessionMode | None = None,
        caller: UserInDB | None = None,
    ) -> list[GeneratedSlotResponse]:
        """Public slot discovery engine. Resolves schedule, exceptions, extra slots, and generates slots."""
        therapist = await self._get_therapist_or_raise(therapist_id)

        # Public visibility access check: must be active and verified unless owner/staff
        is_owner = caller and caller.id == therapist.user_id
        is_staff = caller and any(
            r in caller.roles
            for r in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.STAFF]
        )
        if not (is_owner or is_staff) and (
            therapist.status != TherapistStatus.ACTIVE
            or therapist.verification.status != TherapistVerificationStatus.VERIFIED
        ):
            raise NotFoundException(
                message=f"Therapist with ID '{therapist_id}' not found or not active",
                code=ErrorCode.THERAPIST_NOT_FOUND,
            )

        # Resolve date boundaries
        if target_date:
            try:
                start_d = date.fromisoformat(target_date)
                end_d = start_d
            except ValueError as exc:
                raise BadRequestException(
                    message="Invalid date format. Expected YYYY-MM-DD",
                    code=ErrorCode.INVALID_PARAMETERS,
                ) from exc
        elif start_date and end_date:
            try:
                start_d = date.fromisoformat(start_date)
                end_d = date.fromisoformat(end_date)
            except ValueError as exc:
                raise BadRequestException(
                    message="Invalid date format. Expected YYYY-MM-DD",
                    code=ErrorCode.INVALID_PARAMETERS,
                ) from exc

        else:
            # Default to today
            start_d = date.today()
            end_d = start_d

        if start_d > end_d:
            raise BadRequestException(
                message="start_date cannot be later than end_date",
                code=ErrorCode.INVALID_DATE_RANGE,
            )

        days_count = (end_d - start_d).days + 1
        if days_count > MAX_SLOT_DISCOVERY_DAYS:
            raise BadRequestException(
                message=f"Date range exceeds maximum allowed limit of {MAX_SLOT_DISCOVERY_DAYS} days",
                code=ErrorCode.INVALID_DATE_RANGE,
            )

        # Fetch weekly schedule, exceptions, and extra slots
        schedule = await self.availability_repo.get_weekly_schedule(therapist_id)
        tz_name = schedule.timezone if schedule else DEFAULT_TIMEZONE

        exceptions_list = await self.availability_repo.get_exceptions_for_range(
            therapist_id, start_d.isoformat(), end_d.isoformat()
        )
        exceptions_by_date = {e.date: e for e in exceptions_list}

        extra_slots_list = await self.availability_repo.get_extra_slots_for_range(
            therapist_id, start_d.isoformat(), end_d.isoformat()
        )
        extra_slots_by_date: dict[str, list[ExtraSlotInDB]] = {}
        for es in extra_slots_list:
            extra_slots_by_date.setdefault(es.date, []).append(es)

        # Map weekly schedule by day of week
        schedule_by_day: dict[DayOfWeek, list[DayInterval]] = {}
        if schedule:
            for d in schedule.days:
                schedule_by_day[d.day_of_week] = d.intervals

        duration_minutes = therapist.pricing.duration_minutes
        now_utc = utc_now()
        unavailable_slot_ids = await self.availability_repo.get_unavailable_slot_ids(therapist_id)
        all_slots: list[GeneratedSlotResponse] = []

        curr_d = start_d
        while curr_d <= end_d:
            date_str = curr_d.isoformat()
            day_of_week = DayOfWeek(curr_d.weekday())
            weekly_intervals = schedule_by_day.get(day_of_week, [])
            date_exception = exceptions_by_date.get(date_str)
            date_extras = extra_slots_by_date.get(date_str, [])

            day_slots = generate_slots_for_date(
                therapist_id=therapist_id,
                target_date=curr_d,
                weekly_intervals=weekly_intervals,
                date_exception=date_exception,
                extra_slots=date_extras,
                duration_minutes=duration_minutes,
                session_mode=session_mode,
                therapist_timezone=tz_name,
                current_utc_time=now_utc,
            )
            # Filter out active reservations and pending/confirmed bookings
            available_day_slots = [s for s in day_slots if s.id not in unavailable_slot_ids]
            all_slots.extend(available_day_slots)
            curr_d += timedelta(days=1)

        return all_slots
