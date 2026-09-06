"""Domain business logic for Session lifecycle, attendance, notes, and goals."""

import logging
import uuid
from datetime import UTC, datetime, timedelta

from pymongo.errors import DuplicateKeyError

from app.common.exceptions.app_exceptions import (
    BadRequestException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.common.exceptions.error_codes import ErrorCode
from app.core.config import Settings
from app.modules.booking.booking_model import BookingInDB
from app.modules.booking.booking_repository import BookingRepository
from app.modules.session.providers.google_meet_provider import GoogleMeetProvider
from app.modules.session.providers.meeting_provider import (
    MeetingAttendee,
    MeetingCreationRequest,
    MeetingProvider,
)
from app.modules.session.providers.mock_meeting_provider import MockMeetingProvider
from app.modules.session.session_constants import (
    AttendanceStatus,
    GoalStatus,
    MeetingStatus,
    SessionStatus,
)
from app.modules.session.session_model import (
    SessionInDB,
    SessionMeetingInDB,
    SessionNoteInDB,
    TherapyGoalInDB,
)
from app.modules.session.session_repository import SessionRepository
from app.modules.session.session_schema import (
    ClientSessionNoteResponse,
    ClientSessionResponse,
    CreateTherapyGoalRequest,
    RecordAttendanceRequest,
    SessionNoteResponse,
    SessionResponse,
    TherapistDashboardSummaryResponse,
    TherapyGoalResponse,
    UpdateTherapyGoalRequest,
    UpsertSessionNoteRequest,
)
from app.modules.therapist.therapist_repository import TherapistRepository
from app.modules.user.user_constants import UserRole
from app.modules.user.user_model import UserInDB

logger = logging.getLogger(__name__)


class SessionService:
    """Core domain orchestrator for confirmed session runtimes."""

    def __init__(
        self,
        session_repo: SessionRepository,
        booking_repo: BookingRepository,
        therapist_repo: TherapistRepository,
        settings: Settings,
        meeting_provider: MeetingProvider | None = None,
    ) -> None:
        self.session_repo = session_repo
        self.booking_repo = booking_repo
        self.therapist_repo = therapist_repo
        self.settings = settings
        if meeting_provider is not None:
            self.meeting_provider = meeting_provider
        elif settings.google_calendar_enabled:
            self.meeting_provider = GoogleMeetProvider(
                service_account_email=settings.google_service_account_email,
                private_key=settings.google_service_account_private_key,
                calendar_id=settings.google_calendar_id,
                delegated_user=settings.google_calendar_delegated_user,
            )
        else:
            self.meeting_provider = MockMeetingProvider()

    async def _get_caller_therapist_id(self, caller: UserInDB) -> str | None:
        """Resolve therapist profile ID for authenticated caller if therapist role."""
        if UserRole.THERAPIST in caller.roles:
            th = await self.therapist_repo.get_by_user_id(caller.id)
            if th:
                return th.id
        return None

    # --- Session Lifecycle ---

    async def create_session_for_booking(self, booking: BookingInDB) -> SessionInDB:
        """Deterministic idempotent creation of session from confirmed booking."""
        existing = await self.session_repo.get_session_by_booking_id(booking.id)
        if existing:
            return existing

        is_online = (
            booking.session_mode.value == "online"
            if hasattr(booking.session_mode, "value")
            else str(booking.session_mode) == "online"
        )
        initial_meeting = (
            SessionMeetingInDB(
                provider=self.meeting_provider.name,
                status=MeetingStatus.NOT_STARTED,
            )
            if is_online
            else SessionMeetingInDB(
                provider=self.meeting_provider.name,
                status=MeetingStatus.NOT_REQUIRED,
            )
        )

        session = SessionInDB(
            id=str(uuid.uuid4()),
            booking_id=booking.id,
            therapist_id=booking.therapist_id,
            client_id=booking.client_id,
            scheduled_start_at=booking.start_at,
            scheduled_end_at=booking.end_at,
            duration_minutes=booking.duration_minutes,
            session_mode=booking.session_mode.value if hasattr(booking.session_mode, "value") else str(booking.session_mode),
            status=SessionStatus.SCHEDULED,
            attendance=AttendanceStatus.UNKNOWN,
            meeting=initial_meeting,
        )
        try:
            created = await self.session_repo.create_session(session)
        except DuplicateKeyError:
            existing_after_race = await self.session_repo.get_session_by_booking_id(booking.id)
            if existing_after_race:
                return existing_after_race
            raise

        if is_online:
            try:
                await self.provision_meeting(created.id)
                refreshed = await self.session_repo.get_session_by_id(created.id)
                if refreshed:
                    return refreshed
            except Exception as exc:
                # Meeting provisioning failure must NEVER roll back confirmed booking or session creation.
                logger.error("Initial meeting provisioning failed for session %s: %s", created.id, exc)

        return created

    async def provision_meeting(self, session_id: str) -> SessionInDB:
        """Atomically claim provisioning lock and create conference via MeetingProvider."""
        session = await self.session_repo.get_session_by_id(session_id)
        if not session:
            raise NotFoundException(message="Session not found", code=ErrorCode.SESSION_NOT_FOUND)

        if session.session_mode != "online":
            return session

        # If already ready with join_url, return immediately
        if session.meeting and session.meeting.status == MeetingStatus.READY and session.meeting.join_url:
            return session

        worker_id = str(uuid.uuid4())
        claimed = await self.session_repo.claim_meeting_provisioning(session_id, worker_id=worker_id)
        if not claimed:
            # Another worker has claimed or session is already being provisioned
            fresh = await self.session_repo.get_session_by_id(session_id)
            return fresh or session

        try:
            # 1. Resolve Therapist details
            therapist = await self.therapist_repo.get_by_id(session.therapist_id)
            therapist_name = therapist.display_name if therapist else "Therapist"
            therapist_email = f"therapist_{session.therapist_id}@oppamtherapy.com"
            if therapist and therapist.user_id:
                th_user = await self.session_repo.db["users"].find_one({"id": therapist.user_id})
                if th_user and th_user.get("email"):
                    therapist_email = th_user["email"]

            # 2. Resolve Client details
            client_user = await self.session_repo.db["users"].find_one({"id": session.client_id})
            client_name = "Client"
            client_email = f"client_{session.client_id}@oppamtherapy.com"
            if client_user:
                full_name = f"{client_user.get('first_name', '')} {client_user.get('last_name', '')}".strip()
                if full_name:
                    client_name = full_name
                if client_user.get("email"):
                    client_email = client_user["email"]

            attendees = [
                MeetingAttendee(name=therapist_name, email=therapist_email, role="therapist"),
                MeetingAttendee(name=client_name, email=client_email, role="client"),
            ]

            req = MeetingCreationRequest(
                session_id=session.id,
                title=f"Therapy Session — {therapist_name}",
                start_at=session.scheduled_start_at,
                end_at=session.scheduled_end_at,
                timezone=self.settings.google_calendar_timezone,
                attendees=attendees,
            )

            result = await self.meeting_provider.create_meeting(req)

            meeting_db = SessionMeetingInDB(
                provider=self.meeting_provider.name,
                status=result.status,
                join_url=result.join_url,
                provider_event_id=result.provider_event_id,
                conference_id=result.conference_id,
                error_message=result.error_message,
                claimed_by=None,
                claimed_at=None,
            )
            updated = await self.session_repo.update_session_meeting(session.id, meeting_db)
            return updated or session

        except Exception as exc:
            logger.exception("Failed to provision meeting for session %s: %s", session_id, exc)
            meeting_failed = SessionMeetingInDB(
                provider=self.meeting_provider.name,
                status=MeetingStatus.FAILED,
                error_message=str(exc),
                claimed_by=None,
                claimed_at=None,
            )
            updated = await self.session_repo.update_session_meeting(session.id, meeting_failed)
            return updated or session

    async def retry_meeting_provisioning(
        self, session_id: str, caller: UserInDB
    ) -> SessionResponse:
        """Allow assigned therapist, client, or admin to retry failed meeting provisioning."""
        session = await self.session_repo.get_session_by_id(session_id)
        if not session:
            raise NotFoundException(message="Session not found", code=ErrorCode.SESSION_NOT_FOUND)

        caller_th_id = await self._get_caller_therapist_id(caller)
        is_staff = any(
            r in caller.roles
            for r in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.STAFF]
        )
        is_therapist_owner = caller_th_id == session.therapist_id
        is_client_owner = caller.id == session.client_id

        if not is_therapist_owner and not is_client_owner and not is_staff:
            raise ForbiddenException(
                message="Not authorized to retry meeting for this session",
                code=ErrorCode.FORBIDDEN,
            )

        if session.session_mode != "online":
            raise BadRequestException(
                message="Meeting provisioning is only supported for online sessions",
                code=ErrorCode.SESSION_INVALID_STATE,
            )

        # Force state to failed if stuck in processing so lock claim succeeds
        if session.meeting and session.meeting.status == MeetingStatus.PROCESSING:
            await self.session_repo.update_session_meeting(
                session.id,
                SessionMeetingInDB(
                    provider=self.meeting_provider.name,
                    status=MeetingStatus.FAILED,
                    error_message="Manual retry initiated",
                ),
            )

        updated_session = await self.provision_meeting(session.id)
        return SessionResponse.from_db(updated_session)

    async def get_session(self, session_id: str, caller: UserInDB) -> SessionResponse:
        """Fetch session detail with strict role & ownership checking."""
        session = await self.session_repo.get_session_by_id(session_id)
        if not session:
            raise NotFoundException(message="Session not found", code=ErrorCode.SESSION_NOT_FOUND)

        caller_th_id = await self._get_caller_therapist_id(caller)
        is_staff = any(r in caller.roles for r in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.STAFF])
        is_therapist_owner = caller_th_id == session.therapist_id
        is_client_owner = caller.id == session.client_id

        if not is_therapist_owner and not is_client_owner and not is_staff:
            raise ForbiddenException(
                message="You do not have permission to view this session",
                code=ErrorCode.SESSION_FORBIDDEN,
            )

        return SessionResponse.from_db(session)

    async def get_client_session(self, session_id: str, caller: UserInDB) -> ClientSessionResponse:
        """Client-facing sanitized view of session details."""
        session = await self.session_repo.get_session_by_id(session_id)
        if not session:
            raise NotFoundException(message="Session not found", code=ErrorCode.SESSION_NOT_FOUND)

        if session.client_id != caller.id:
            raise ForbiddenException(
                message="Session belongs to another client",
                code=ErrorCode.SESSION_FORBIDDEN,
            )
        return ClientSessionResponse.from_db(session)

    async def start_session(self, session_id: str, caller: UserInDB) -> SessionResponse:
        """Start a session within the configured window (Therapist only)."""
        session = await self.session_repo.get_session_by_id(session_id)
        if not session:
            raise NotFoundException(message="Session not found", code=ErrorCode.SESSION_NOT_FOUND)

        caller_th_id = await self._get_caller_therapist_id(caller)
        is_staff = any(r in caller.roles for r in [UserRole.ADMIN, UserRole.SUPER_ADMIN])
        if caller_th_id != session.therapist_id and not is_staff:
            raise ForbiddenException(
                message="Only the assigned therapist can start this session",
                code=ErrorCode.SESSION_FORBIDDEN,
            )

        # Idempotency check: if already IN_PROGRESS, return current state
        if session.status == SessionStatus.IN_PROGRESS:
            return SessionResponse.from_db(session)

        if session.status == SessionStatus.COMPLETED:
            raise BadRequestException(
                message="Session has already been completed",
                code=ErrorCode.SESSION_ALREADY_COMPLETED,
            )
        if session.status == SessionStatus.CANCELLED:
            raise BadRequestException(
                message="Session has been cancelled",
                code=ErrorCode.SESSION_INVALID_STATE,
            )

        # Session timing window check
        now = datetime.now(UTC)
        start_allowed_from = session.scheduled_start_at - timedelta(
            minutes=self.settings.session_start_window_minutes
        )
        end_allowed_until = session.scheduled_end_at + timedelta(
            minutes=self.settings.session_grace_period_minutes
        )

        if now < start_allowed_from:
            raise BadRequestException(
                message=f"Session cannot be started yet. You can start up to {self.settings.session_start_window_minutes} minutes before scheduled time.",
                code=ErrorCode.SESSION_START_TOO_EARLY,
            )
        if now > end_allowed_until:
            raise BadRequestException(
                message="Session scheduled window has passed and is expired.",
                code=ErrorCode.SESSION_START_TOO_LATE,
            )

        # Atomic state transition
        started_session = await self.session_repo.start_session_atomic(session.id, started_at=now)
        if not started_session:
            # Check if concurrent request already transitioned it
            latest = await self.session_repo.get_session_by_id(session.id)
            if latest and latest.status == SessionStatus.IN_PROGRESS:
                return SessionResponse.from_db(latest)
            raise ConflictException(
                message="Unable to start session due to state conflict",
                code=ErrorCode.SESSION_INVALID_STATE,
            )

        return SessionResponse.from_db(started_session)

    async def complete_session(self, session_id: str, caller: UserInDB) -> SessionResponse:
        """Mark session completed (Therapist only)."""
        session = await self.session_repo.get_session_by_id(session_id)
        if not session:
            raise NotFoundException(message="Session not found", code=ErrorCode.SESSION_NOT_FOUND)

        caller_th_id = await self._get_caller_therapist_id(caller)
        is_staff = any(r in caller.roles for r in [UserRole.ADMIN, UserRole.SUPER_ADMIN])
        if caller_th_id != session.therapist_id and not is_staff:
            raise ForbiddenException(
                message="Only the assigned therapist can complete this session",
                code=ErrorCode.SESSION_FORBIDDEN,
            )

        # Idempotency check: if already completed, return current state
        if session.status == SessionStatus.COMPLETED:
            return SessionResponse.from_db(session)

        if session.status != SessionStatus.IN_PROGRESS:
            raise BadRequestException(
                message="Only sessions currently in progress can be completed",
                code=ErrorCode.SESSION_INVALID_STATE,
            )

        now = datetime.now(UTC)
        completed_session = await self.session_repo.complete_session_atomic(session.id, ended_at=now)
        if not completed_session:
            latest = await self.session_repo.get_session_by_id(session.id)
            if latest and latest.status == SessionStatus.COMPLETED:
                return SessionResponse.from_db(latest)
            raise ConflictException(
                message="Unable to complete session due to state conflict",
                code=ErrorCode.SESSION_INVALID_STATE,
            )

        # Default attendance to PRESENT if still UNKNOWN upon completion
        if completed_session.attendance == AttendanceStatus.UNKNOWN:
            updated = await self.session_repo.update_attendance(session.id, AttendanceStatus.PRESENT)
            if updated:
                completed_session = updated

        return SessionResponse.from_db(completed_session)

    async def record_attendance(
        self, session_id: str, caller: UserInDB, req: RecordAttendanceRequest
    ) -> SessionResponse:
        """Record attendance for session (Therapist only)."""
        session = await self.session_repo.get_session_by_id(session_id)
        if not session:
            raise NotFoundException(message="Session not found", code=ErrorCode.SESSION_NOT_FOUND)

        caller_th_id = await self._get_caller_therapist_id(caller)
        is_staff = any(r in caller.roles for r in [UserRole.ADMIN, UserRole.SUPER_ADMIN])
        if caller_th_id != session.therapist_id and not is_staff:
            raise ForbiddenException(
                message="Only the assigned therapist can record attendance",
                code=ErrorCode.SESSION_FORBIDDEN,
            )

        updated = await self.session_repo.update_attendance(session.id, req.attendance)
        if not updated:
            raise NotFoundException(message="Session not found", code=ErrorCode.SESSION_NOT_FOUND)
        return SessionResponse.from_db(updated)

    # --- Clinical Notes Operations ---

    async def get_session_note(self, session_id: str, caller: UserInDB) -> SessionNoteResponse:
        """Therapist retrieval of full clinical notes including confidential private notes."""
        session = await self.session_repo.get_session_by_id(session_id)
        if not session:
            raise NotFoundException(message="Session not found", code=ErrorCode.SESSION_NOT_FOUND)

        caller_th_id = await self._get_caller_therapist_id(caller)
        is_staff = any(r in caller.roles for r in [UserRole.ADMIN, UserRole.SUPER_ADMIN])
        if caller_th_id != session.therapist_id and not is_staff:
            raise ForbiddenException(
                message="Private clinical notes are restricted to the assigned therapist",
                code=ErrorCode.SESSION_NOTE_FORBIDDEN,
            )

        note = await self.session_repo.get_note_by_session_id(session_id)
        if not note:
            # Return empty note representation
            now = datetime.now(UTC)
            note = SessionNoteInDB(
                id=str(uuid.uuid4()),
                session_id=session.id,
                therapist_id=session.therapist_id,
                client_id=session.client_id,
                summary="",
                private_notes="",
                created_at=now,
                updated_at=now,
            )
        return SessionNoteResponse.from_db(note)

    async def get_client_session_note(self, session_id: str, caller: UserInDB) -> ClientSessionNoteResponse:
        """Client view: returns ONLY public summary, zero private clinical notes."""
        session = await self.session_repo.get_session_by_id(session_id)
        if not session:
            raise NotFoundException(message="Session not found", code=ErrorCode.SESSION_NOT_FOUND)

        if session.client_id != caller.id:
            raise ForbiddenException(
                message="Session belongs to another client",
                code=ErrorCode.SESSION_NOTE_FORBIDDEN,
            )

        note = await self.session_repo.get_note_by_session_id(session_id)
        if not note:
            now = datetime.now(UTC)
            return ClientSessionNoteResponse(session_id=session_id, summary="", updated_at=now)
        return ClientSessionNoteResponse.from_db(note)

    async def upsert_session_note(
        self, session_id: str, caller: UserInDB, req: UpsertSessionNoteRequest
    ) -> SessionNoteResponse:
        """Upsert clinical notes (Therapist only)."""
        session = await self.session_repo.get_session_by_id(session_id)
        if not session:
            raise NotFoundException(message="Session not found", code=ErrorCode.SESSION_NOT_FOUND)

        caller_th_id = await self._get_caller_therapist_id(caller)
        is_staff = any(r in caller.roles for r in [UserRole.ADMIN, UserRole.SUPER_ADMIN])
        if caller_th_id != session.therapist_id and not is_staff:
            raise ForbiddenException(
                message="Only the assigned therapist can modify clinical notes",
                code=ErrorCode.SESSION_NOTE_FORBIDDEN,
            )

        now = datetime.now(UTC)
        note_in = SessionNoteInDB(
            id=str(uuid.uuid4()),
            session_id=session.id,
            therapist_id=session.therapist_id,
            client_id=session.client_id,
            summary=req.summary,
            private_notes=req.private_notes,
            created_at=now,
            updated_at=now,
        )
        saved = await self.session_repo.upsert_note(note_in)
        return SessionNoteResponse.from_db(saved)

    # --- Therapy Goals Operations ---

    async def create_goal(
        self, session_id: str, caller: UserInDB, req: CreateTherapyGoalRequest
    ) -> TherapyGoalResponse:
        """Create a new client therapy goal (Therapist only)."""
        session = await self.session_repo.get_session_by_id(session_id)
        if not session:
            raise NotFoundException(message="Session not found", code=ErrorCode.SESSION_NOT_FOUND)

        caller_th_id = await self._get_caller_therapist_id(caller)
        is_staff = any(r in caller.roles for r in [UserRole.ADMIN, UserRole.SUPER_ADMIN])
        if caller_th_id != session.therapist_id and not is_staff:
            raise ForbiddenException(
                message="Only the assigned therapist can establish therapy goals",
                code=ErrorCode.SESSION_GOAL_FORBIDDEN,
            )

        goal = TherapyGoalInDB(
            id=str(uuid.uuid4()),
            session_id=session.id,
            therapist_id=session.therapist_id,
            client_id=session.client_id,
            title=req.title,
            description=req.description,
            status=GoalStatus.ACTIVE,
        )
        saved = await self.session_repo.create_goal(goal)
        return TherapyGoalResponse.from_db(saved)

    async def list_goals(self, session_id: str, caller: UserInDB) -> list[TherapyGoalResponse]:
        """List therapy goals for the client associated with this session."""
        session = await self.session_repo.get_session_by_id(session_id)
        if not session:
            raise NotFoundException(message="Session not found", code=ErrorCode.SESSION_NOT_FOUND)

        caller_th_id = await self._get_caller_therapist_id(caller)
        is_staff = any(r in caller.roles for r in [UserRole.ADMIN, UserRole.SUPER_ADMIN])
        if caller_th_id != session.therapist_id and caller.id != session.client_id and not is_staff:
            raise ForbiddenException(
                message="You do not have permission to view these therapy goals",
                code=ErrorCode.SESSION_GOAL_FORBIDDEN,
            )

        goals = await self.session_repo.list_goals_by_session(session.id)
        return [TherapyGoalResponse.from_db(g) for g in goals]

    async def list_client_goals(self, client_id: str, caller: UserInDB) -> list[TherapyGoalResponse]:
        """List all historical therapy goals for a client across all sessions."""
        is_owner = caller.id == client_id
        is_staff = any(r in caller.roles for r in [UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.STAFF])
        caller_th_id = await self._get_caller_therapist_id(caller)
        if not is_owner and not is_staff and not caller_th_id:
            raise ForbiddenException(
                message="You do not have permission to view this client's goals",
                code=ErrorCode.SESSION_GOAL_FORBIDDEN,
            )

        goals = await self.session_repo.list_client_goals(client_id)
        return [TherapyGoalResponse.from_db(g) for g in goals]

    async def update_goal(
        self, goal_id: str, caller: UserInDB, req: UpdateTherapyGoalRequest
    ) -> TherapyGoalResponse:
        """Update therapy goal status or description (Therapist only)."""
        goal = await self.session_repo.get_goal_by_id(goal_id)
        if not goal:
            raise NotFoundException(message="Goal not found", code=ErrorCode.SESSION_GOAL_NOT_FOUND)

        caller_th_id = await self._get_caller_therapist_id(caller)
        is_staff = any(r in caller.roles for r in [UserRole.ADMIN, UserRole.SUPER_ADMIN])
        if caller_th_id != goal.therapist_id and not is_staff:
            raise ForbiddenException(
                message="Only the assigned therapist can modify this goal",
                code=ErrorCode.SESSION_GOAL_FORBIDDEN,
            )

        updated = await self.session_repo.update_goal(
            goal_id=goal_id,
            title=req.title,
            description=req.description,
            status=req.status,
        )
        if not updated:
            raise NotFoundException(message="Goal not found", code=ErrorCode.SESSION_GOAL_NOT_FOUND)
        return TherapyGoalResponse.from_db(updated)

    # --- Therapist Portal Aggregations ---

    async def get_therapist_dashboard(self, caller: UserInDB) -> TherapistDashboardSummaryResponse:
        """Aggregated daily agenda and operational summary for therapist portal."""
        caller_th_id = await self._get_caller_therapist_id(caller)
        if not caller_th_id:
            raise ForbiddenException(
                message="User does not have an active therapist profile",
                code=ErrorCode.THERAPIST_NOT_FOUND,
            )

        now = datetime.now(UTC)
        start_of_today = datetime(now.year, now.month, now.day, 0, 0, 0, tzinfo=UTC)
        end_of_today = datetime(now.year, now.month, now.day, 23, 59, 59, tzinfo=UTC)

        today_sessions, today_count = await self.session_repo.find_therapist_sessions(
            therapist_id=caller_th_id,
            start_min=start_of_today,
            start_max=end_of_today,
            limit=50,
        )
        _, upcoming_count = await self.session_repo.find_therapist_sessions(
            therapist_id=caller_th_id,
            start_min=now,
            status=SessionStatus.SCHEDULED,
            limit=1,
        )
        _, completed_count = await self.session_repo.find_therapist_sessions(
            therapist_id=caller_th_id,
            status=SessionStatus.COMPLETED,
            limit=1,
        )

        return TherapistDashboardSummaryResponse(
            today_sessions_count=today_count,
            upcoming_sessions_count=upcoming_count,
            completed_sessions_count=completed_count,
            today_sessions=[SessionResponse.from_db(s) for s in today_sessions],
        )

    async def list_therapist_sessions(
        self,
        caller: UserInDB,
        status: SessionStatus | None = None,
        date_filter: str | None = None,
        skip: int = 0,
        limit: int = 50,
    ) -> list[SessionResponse]:
        """List sessions for authenticated therapist."""
        caller_th_id = await self._get_caller_therapist_id(caller)
        if not caller_th_id:
            raise ForbiddenException(
                message="User does not have a therapist profile",
                code=ErrorCode.THERAPIST_NOT_FOUND,
            )

        start_min: datetime | None = None
        start_max: datetime | None = None
        if date_filter:
            d = datetime.strptime(date_filter, "%Y-%m-%d")
            start_min = datetime(d.year, d.month, d.day, 0, 0, 0, tzinfo=UTC)
            start_max = datetime(d.year, d.month, d.day, 23, 59, 59, tzinfo=UTC)

        sessions, _ = await self.session_repo.find_therapist_sessions(
            therapist_id=caller_th_id,
            start_min=start_min,
            start_max=start_max,
            status=status,
            skip=skip,
            limit=limit,
        )
        return [SessionResponse.from_db(s) for s in sessions]

    async def list_client_sessions(
        self, caller: UserInDB, status: SessionStatus | None = None, skip: int = 0, limit: int = 50
    ) -> list[ClientSessionResponse]:
        """List client's upcoming and completed sessions."""
        sessions, _ = await self.session_repo.find_client_sessions(
            client_id=caller.id,
            status=status,
            skip=skip,
            limit=limit,
        )
        return [ClientSessionResponse.from_db(s) for s in sessions]
