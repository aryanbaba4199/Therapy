"""Business domain workflows and concurrency orchestration for Reservations and Bookings."""

import contextlib
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from pymongo.errors import DuplicateKeyError

from app.common.exceptions.app_exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.common.exceptions.error_codes import ErrorCode
from app.common.pagination.pagination import PaginatedData, PaginationMeta, PaginationParams
from app.core.config import Settings
from app.modules.availability.availability_service import AvailabilityService
from app.modules.booking.booking_constants import (
    VALID_BOOKING_STATUS_TRANSITIONS,
    BookingStatus,
    ReservationStatus,
)
from app.modules.booking.booking_model import (
    BookingInDB,
    ClientSnapshot,
    PricingSnapshot,
    ReservationInDB,
    TherapistSnapshot,
)
from app.modules.booking.booking_repository import BookingRepository
from app.modules.booking.booking_schema import (
    BookingDetailResponse,
    BookingMeetingResponse,
    BookingSummaryResponse,
    CancelBookingRequest,
    ConfirmBookingRequest,
    CreateReservationRequest,
    ReservationResponse,
)
from app.modules.therapist.therapist_constants import (
    TherapistStatus,
    TherapistVerificationStatus,
)
from app.modules.therapist.therapist_repository import TherapistRepository
from app.modules.user.user_constants import UserRole
from app.modules.user.user_model import UserInDB


class BookingService:
    """Domain service managing temporary slot reservations and confirmed bookings."""

    def __init__(
        self,
        booking_repo: BookingRepository,
        therapist_repo: TherapistRepository,
        availability_service: AvailabilityService,
        settings: Settings,
        session_service: Any = None,
    ) -> None:
        self.booking_repo = booking_repo
        self.therapist_repo = therapist_repo
        self.availability_service = availability_service
        self.settings = settings

        if session_service is not None:
            self.session_service = session_service
        else:
            from app.modules.session.session_repository import SessionRepository
            from app.modules.session.session_service import SessionService
            sess_repo = SessionRepository(booking_repo.db)
            self.session_service = SessionService(
                session_repo=sess_repo,
                booking_repo=booking_repo,
                therapist_repo=therapist_repo,
                settings=settings,
            )



    def _extract_meeting_response(self, meeting_obj: Any) -> BookingMeetingResponse | None:
        """Helper to safely construct BookingMeetingResponse from doc or model."""
        if not meeting_obj:
            return None
        if isinstance(meeting_obj, dict):
            provider = str(meeting_obj.get("provider", ""))
            status = str(meeting_obj.get("status", ""))
            join_url = meeting_obj.get("join_url")
        else:
            provider = str(getattr(meeting_obj, "provider", ""))
            status = str(getattr(meeting_obj, "status", ""))
            join_url = getattr(meeting_obj, "join_url", None)
        if not provider or not status:
            return None
        return BookingMeetingResponse(provider=provider, status=status, join_url=join_url)

    async def _build_booking_detail_response(self, booking: BookingInDB) -> BookingDetailResponse:
        """Helper to construct BookingDetailResponse with linked session and Google Meet details."""
        session_id = None
        meeting = None
        if self.session_service:
            sess = await self.session_service.session_repo.get_session_by_booking_id(booking.id)
            if sess:
                session_id = sess.id
                meeting = self._extract_meeting_response(sess.meeting)
        return BookingDetailResponse.from_db(booking, session_id=session_id, meeting=meeting)

    async def create_reservation(
        self, caller: UserInDB, req: CreateReservationRequest
    ) -> ReservationResponse:
        """Atomically reserve an available consultation slot with configurable TTL."""
        # 1. Verify therapist exists and is active & verified
        therapist = await self.therapist_repo.get_by_id(req.therapist_id)
        if not therapist:
            raise NotFoundException(
                message="Therapist not found",
                code=ErrorCode.THERAPIST_NOT_FOUND,
            )
        if (
            therapist.status != TherapistStatus.ACTIVE
            or therapist.verification.status != TherapistVerificationStatus.VERIFIED
        ):
            raise BadRequestException(
                message="Therapist is not currently accepting bookings",
                code=ErrorCode.INVALID_THERAPIST_STATUS,
            )

        # 2. Check if an active reservation or confirmed booking exists for this slot
        now = datetime.now(UTC)
        existing_res = await self.booking_repo.get_active_reservation_for_slot(
            req.therapist_id, req.slot_id
        )
        if existing_res:
            if existing_res.expires_at < now:
                await self.booking_repo.update_reservation_status(
                    existing_res.id, ReservationStatus.EXPIRED
                )
            elif existing_res.client_id == caller.id:
                # Same user holds active reservation: return it
                return ReservationResponse.from_db(existing_res)
            else:
                raise ConflictException(
                    message="This slot is currently held by another client",
                    code=ErrorCode.BOOKING_SLOT_UNAVAILABLE,
                )

        # 3. Check Phase 4 slot engine availability for the requested date and session mode
        generated_slots = await self.availability_service.get_available_slots(
            therapist_id=req.therapist_id,
            target_date=req.slot_date,
            session_mode=req.session_mode,
            caller=caller,
        )

        matched_slot = next((s for s in generated_slots if s.id == req.slot_id), None)
        if not matched_slot:
            # Check if it was filtered out because it is reserved or booked
            if existing_res and existing_res.expires_at >= now:
                raise ConflictException(
                    message="This slot is currently held by another client",
                    code=ErrorCode.BOOKING_SLOT_UNAVAILABLE,
                )
            raise NotFoundException(
                message="Slot not found or is no longer available",
                code=ErrorCode.BOOKING_SLOT_NOT_FOUND,
            )

        # 4. Verify slot is not in the past
        if matched_slot.start_at <= now:
            raise BadRequestException(
                message="Cannot reserve a slot in the past",
                code=ErrorCode.DATE_IN_PAST,
            )

        # 5. Build new reservation with configured TTL
        ttl_seconds = self.settings.booking_reservation_ttl_seconds
        expires_at = now + timedelta(seconds=ttl_seconds)

        reservation = ReservationInDB(
            id=str(uuid.uuid4()),
            slot_id=matched_slot.id,
            therapist_id=matched_slot.therapist_id,
            client_id=caller.id,
            session_mode=matched_slot.session_mode,
            start_at=matched_slot.start_at,
            end_at=matched_slot.end_at,
            duration_minutes=therapist.pricing.duration_minutes,
            status=ReservationStatus.ACTIVE,
            reserved_at=now,
            expires_at=expires_at,
            created_at=now,
            updated_at=now,
        )

        # 6. Atomic insertion protected by MongoDB unique partial index
        try:
            saved = await self.booking_repo.create_reservation(reservation)
        except DuplicateKeyError:
            raise ConflictException(
                message="This slot was just reserved by another client",
                code=ErrorCode.BOOKING_SLOT_UNAVAILABLE,
            ) from None

        return ReservationResponse.from_db(saved)

    async def get_reservation(
        self, caller: UserInDB, reservation_id: str
    ) -> ReservationResponse:
        """Fetch reservation details with active countdown timer."""
        reservation = await self.booking_repo.get_reservation_by_id(reservation_id)
        if not reservation:
            raise NotFoundException(
                message="Reservation not found",
                code=ErrorCode.BOOKING_RESERVATION_NOT_FOUND,
            )

        # Authorization: caller must be client, therapist, or staff
        is_owner = caller.id == reservation.client_id
        is_staff = any(
            r in caller.roles
            for r in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.STAFF]
        )
        if not is_owner and not is_staff:
            raise ForbiddenException(
                message="You do not have permission to view this reservation",
                code=ErrorCode.BOOKING_RESERVATION_FORBIDDEN,
            )

        # Auto-expire if past expiry
        now = datetime.now(UTC)
        if reservation.status == ReservationStatus.ACTIVE and reservation.expires_at < now:
            updated = await self.booking_repo.update_reservation_status(
                reservation.id, ReservationStatus.EXPIRED
            )
            if updated:
                reservation = updated

        return ReservationResponse.from_db(reservation)

    async def cancel_reservation(self, caller: UserInDB, reservation_id: str) -> bool:
        """Cancel and release an active slot reservation."""
        reservation = await self.booking_repo.get_reservation_by_id(reservation_id)
        if not reservation:
            raise NotFoundException(
                message="Reservation not found",
                code=ErrorCode.BOOKING_RESERVATION_NOT_FOUND,
            )

        is_owner = caller.id == reservation.client_id
        is_staff = any(
            r in caller.roles
            for r in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.STAFF]
        )
        if not is_owner and not is_staff:
            raise ForbiddenException(
                message="You do not have permission to cancel this reservation",
                code=ErrorCode.BOOKING_RESERVATION_FORBIDDEN,
            )

        updated = await self.booking_repo.transition_reservation_status(
            reservation_id=reservation.id,
            from_status=ReservationStatus.ACTIVE,
            to_status=ReservationStatus.CANCELLED,
        )
        if not updated:
            latest = await self.booking_repo.get_reservation_by_id(reservation.id)
            if latest and latest.status == ReservationStatus.CANCELLED:
                return True
            raise BadRequestException(
                message=f"Cannot cancel reservation in '{latest.status if latest else 'unknown'}' status",
                code=ErrorCode.BOOKING_RESERVATION_EXPIRED,
            )
        return True

    async def confirm_booking(
        self, caller: UserInDB, req: ConfirmBookingRequest
    ) -> BookingDetailResponse:
        """Confirm booking from an active reservation. Idempotent on retry."""
        # 1. Fetch reservation
        reservation = await self.booking_repo.get_reservation_by_id(req.reservation_id)
        if not reservation:
            raise NotFoundException(
                message="Reservation not found",
                code=ErrorCode.BOOKING_RESERVATION_NOT_FOUND,
            )

        # 2. Ownership check
        if reservation.client_id != caller.id:
            raise ForbiddenException(
                message="Reservation belongs to another client",
                code=ErrorCode.BOOKING_RESERVATION_FORBIDDEN,
            )

        # 3. Idempotency: return existing booking if already confirmed
        existing_booking = await self.booking_repo.get_booking_by_reservation_id(
            req.reservation_id
        )
        if existing_booking:
            return await self._build_booking_detail_response(existing_booking)

        # 4. Check reservation state and expiration with atomic transition
        now = datetime.now(UTC)
        if reservation.status != ReservationStatus.ACTIVE or reservation.expires_at < now:
            if reservation.status == ReservationStatus.ACTIVE:
                await self.booking_repo.update_reservation_status(
                    reservation.id, ReservationStatus.EXPIRED
                )
            raise BadRequestException(
                message="Reservation has expired or is no longer active",
                code=ErrorCode.BOOKING_RESERVATION_EXPIRED,
            )

        # Atomically transition ACTIVE -> CONVERTED
        converted = await self.booking_repo.transition_reservation_status(
            reservation_id=reservation.id,
            from_status=ReservationStatus.ACTIVE,
            to_status=ReservationStatus.CONVERTED,
            require_unexpired=True,
        )
        if not converted:
            existing_booking = await self.booking_repo.get_booking_by_reservation_id(
                req.reservation_id
            )
            if existing_booking:
                return await self._build_booking_detail_response(existing_booking)
            raise BadRequestException(
                message="Reservation has expired or is no longer active",
                code=ErrorCode.BOOKING_RESERVATION_EXPIRED,
            )

        # 5. Fetch therapist for snapshots
        therapist = await self.therapist_repo.get_by_id(reservation.therapist_id)
        if not therapist:
            raise NotFoundException(
                message="Therapist profile not found",
                code=ErrorCode.THERAPIST_NOT_FOUND,
            )

        pricing_snapshot = PricingSnapshot(
            amount=therapist.pricing.amount,
            currency=therapist.pricing.currency,
            duration_minutes=reservation.duration_minutes,
        )
        therapist_snapshot = TherapistSnapshot(
            id=therapist.id,
            display_name=therapist.display_name,
            designation=therapist.designation,
            specialization=therapist.specialization.value,
            profile_image_url=therapist.profile_image_url,
        )
        client_snapshot = ClientSnapshot(
            id=caller.id,
            first_name=caller.first_name,
            last_name=caller.last_name,
            email=caller.email,
            phone=caller.phone,
        )

        booking = BookingInDB(
            id=str(uuid.uuid4()),
            client_id=caller.id,
            therapist_id=therapist.id,
            slot_id=reservation.slot_id,
            reservation_id=reservation.id,
            session_mode=reservation.session_mode,
            start_at=reservation.start_at,
            end_at=reservation.end_at,
            duration_minutes=reservation.duration_minutes,
            status=BookingStatus.CONFIRMED,
            pricing=pricing_snapshot,
            therapist=therapist_snapshot,
            client=client_snapshot,
            notes=req.notes,
            created_at=now,
            updated_at=now,
        )

        try:
            saved_booking = await self.booking_repo.create_booking(booking)
        except DuplicateKeyError:
            existing = await self.booking_repo.get_booking_by_reservation_id(reservation.id)
            if existing:
                return await self._build_booking_detail_response(existing)
            raise ConflictException(
                message="This slot has already been booked",
                code=ErrorCode.BOOKING_ALREADY_EXISTS,
            ) from None

        # 6. Create scheduled session idempotently
        if self.session_service:
            await self.session_service.create_session_for_booking(saved_booking)

        return await self._build_booking_detail_response(saved_booking)



    async def list_client_bookings(
        self,
        caller: UserInDB,
        pagination: PaginationParams,
        status_filter: list[BookingStatus] | None = None,
    ) -> PaginatedData[BookingSummaryResponse]:
        """List paginated bookings for current authenticated client."""
        skip = (pagination.page - 1) * pagination.limit
        bookings, total = await self.booking_repo.find_client_bookings(
            client_id=caller.id,
            status_filter=status_filter,
            skip=skip,
            limit=pagination.limit,
        )

        session_map: dict[str, Any] = {}
        if self.session_service and bookings:
            booking_ids = [b.id for b in bookings]
            cursor = self.session_service.session_repo.sessions.find(
                {"booking_id": {"$in": booking_ids}}
            )
            async for s_doc in cursor:
                session_map[s_doc["booking_id"]] = s_doc

        meta = PaginationMeta.create(
            page=pagination.page,
            limit=pagination.limit,
            total_items=total,
        )
        items = []
        for b in bookings:
            s_doc = session_map.get(b.id)
            s_id = s_doc.get("id") if s_doc else None
            meeting_raw = s_doc.get("meeting") if s_doc else None
            m_resp = self._extract_meeting_response(meeting_raw)
            items.append(
                BookingSummaryResponse.from_db(b, session_id=s_id, meeting=m_resp)
            )
        return PaginatedData(items=items, pagination=meta)

    async def get_booking_detail(
        self, caller: UserInDB, booking_id: str
    ) -> BookingDetailResponse:
        """Retrieve booking detail by UUID with authorization."""
        booking = await self.booking_repo.get_booking_by_id(booking_id)
        if not booking:
            booking = await self.booking_repo.get_booking_by_reservation_id(booking_id)
        if not booking:
            raise NotFoundException(
                message="Booking not found",
                code=ErrorCode.BOOKING_NOT_FOUND,
            )

        # Authorized if client, therapist, or staff
        is_client = caller.id == booking.client_id
        is_staff = any(
            r in caller.roles
            for r in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.STAFF]
        )
        if not is_client and not is_staff:
            # Check if caller is the therapist owner
            therapist = await self.therapist_repo.get_by_id(booking.therapist_id)
            if not therapist or therapist.user_id != caller.id:
                raise ForbiddenException(
                    message="You do not have permission to view this booking",
                    code=ErrorCode.FORBIDDEN,
                )

        session_id = None
        meeting = None
        if self.session_service:
            sess = await self.session_service.session_repo.get_session_by_booking_id(booking.id)
            if sess:
                session_id = sess.id
                meeting = self._extract_meeting_response(sess.meeting)

        return BookingDetailResponse.from_db(
            booking, session_id=session_id, meeting=meeting
        )

    async def cancel_booking(
        self, caller: UserInDB, booking_id: str, req: CancelBookingRequest
    ) -> BookingDetailResponse:
        """Cancel a confirmed booking."""
        booking = await self.booking_repo.get_booking_by_id(booking_id)
        if not booking:
            raise NotFoundException(
                message="Booking not found",
                code=ErrorCode.BOOKING_NOT_FOUND,
            )

        is_client = caller.id == booking.client_id
        is_staff = any(
            r in caller.roles
            for r in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.STAFF]
        )
        if not is_client and not is_staff:
            therapist = await self.therapist_repo.get_by_id(booking.therapist_id)
            if not therapist or therapist.user_id != caller.id:
                raise ForbiddenException(
                    message="You do not have permission to cancel this booking",
                    code=ErrorCode.FORBIDDEN,
                )

        # Validate transition
        allowed_transitions = VALID_BOOKING_STATUS_TRANSITIONS.get(booking.status, set())
        if BookingStatus.CANCELLED not in allowed_transitions:
            raise BadRequestException(
                message=f"Cannot cancel a booking in '{booking.status}' status",
                code=ErrorCode.BOOKING_CANCEL_NOT_ALLOWED,
            )

        # Check linked session status
        if self.session_service:
            session = await self.session_service.session_repo.get_session_by_booking_id(booking_id)
            if session:
                from app.modules.session.session_constants import SessionStatus
                if session.status in [SessionStatus.IN_PROGRESS, SessionStatus.COMPLETED]:
                    raise BadRequestException(
                        message=f"Cannot cancel booking for a session that is '{session.status.value}'",
                        code=ErrorCode.BOOKING_CANCEL_NOT_ALLOWED,
                    )

        updated = await self.booking_repo.update_booking_status(
            booking_id=booking_id,
            status=BookingStatus.CANCELLED,
            cancellation_reason=req.reason,
            cancelled_by=caller.id,
        )
        if not updated:
            raise NotFoundException(
                message="Booking not found during update",
                code=ErrorCode.BOOKING_NOT_FOUND,
            )

        if self.session_service:
            with contextlib.suppress(Exception):
                session = await self.session_service.session_repo.get_session_by_booking_id(booking_id)
                if session:
                    await self.session_service.session_repo.cancel_session(session.id)

        return BookingDetailResponse.from_db(updated)


