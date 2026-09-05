"""Core domain service for Support Ticket lifecycle, reference IDOR checks, and conversations."""

import uuid
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.common.exceptions.app_exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
)
from app.common.exceptions.error_codes import ErrorCode
from app.common.utils.datetime_utils import utc_now
from app.modules.support.support_constants import (
    SupportCategory,
    SupportPriority,
    SupportTicketStatus,
)
from app.modules.support.support_model import (
    SupportMessageInDB,
    SupportTicketInDB,
)
from app.modules.support.support_repository import SupportRepository
from app.modules.support.support_schema import (
    CreateSupportMessageRequest,
    CreateSupportTicketRequest,
    SupportMessageResponse,
    SupportTicketResponse,
)
from app.modules.user.user_constants import UserRole
from app.modules.user.user_model import UserInDB


class SupportService:
    """Service handling support inquiries, authorization boundaries, and message threads."""

    def __init__(
        self,
        db: AsyncIOMotorDatabase[dict[str, Any]],
        support_repo: SupportRepository | None = None,
    ) -> None:
        self.db = db
        self.support_repo = support_repo or SupportRepository(db)

    def _is_staff_or_admin(self, user: UserInDB) -> bool:
        """Check if user has customer support / staff authorization."""
        return any(
            role
            in [
                UserRole.STAFF,
                UserRole.FIRST_RESPONDER,
                UserRole.ADMIN,
                UserRole.SUPER_ADMIN,
            ]
            for role in user.roles
        )

    async def _validate_references(
        self, caller: UserInDB, req: CreateSupportTicketRequest
    ) -> None:
        """Strict reference validation to prevent IDOR vulnerabilities."""
        is_staff = self._is_staff_or_admin(caller)

        # 1. Booking Reference Validation
        if req.booking_id:
            booking = await self.db.get_collection("bookings").find_one(
                {"id": req.booking_id}
            )
            if not booking:
                raise NotFoundException(
                    message=f"Referenced booking '{req.booking_id}' does not exist.",
                    code=ErrorCode.BOOKING_NOT_FOUND,
                )
            if not is_staff and booking.get("client_id") != caller.id:
                raise ForbiddenException(
                    message="You cannot reference a booking that does not belong to you.",
                    code=ErrorCode.SUPPORT_TICKET_REFERENCE_FORBIDDEN,
                )

        # 2. Payment Reference Validation
        if req.payment_id:
            payment = await self.db.get_collection("payments").find_one(
                {"id": req.payment_id}
            )
            if not payment:
                raise NotFoundException(
                    message=f"Referenced payment '{req.payment_id}' does not exist.",
                    code=ErrorCode.PAYMENT_NOT_FOUND,
                )
            if not is_staff and payment.get("user_id") != caller.id:
                raise ForbiddenException(
                    message="You cannot reference a payment that does not belong to you.",
                    code=ErrorCode.SUPPORT_TICKET_REFERENCE_FORBIDDEN,
                )

        # 3. Package Reference Validation
        if req.package_id:
            package = await self.db.get_collection("user_packages").find_one(
                {"id": req.package_id}
            )
            if not package:
                raise NotFoundException(
                    message=f"Referenced package '{req.package_id}' does not exist.",
                    code=ErrorCode.PACKAGE_NOT_FOUND,
                )
            if not is_staff and package.get("user_id") != caller.id:
                raise ForbiddenException(
                    message="You cannot reference a package that does not belong to you.",
                    code=ErrorCode.SUPPORT_TICKET_REFERENCE_FORBIDDEN,
                )

        # 4. Session Reference Validation
        if req.session_id:
            session = await self.db.get_collection("sessions").find_one(
                {"id": req.session_id}
            )
            if not session:
                raise NotFoundException(
                    message=f"Referenced session '{req.session_id}' does not exist.",
                    code=ErrorCode.SESSION_NOT_FOUND,
                )
            # Allow client or therapist of that session
            client_owns = session.get("client_id") == caller.id
            therapist_owns = False
            if UserRole.THERAPIST in caller.roles:
                therapist_profile = await self.db.get_collection("therapists").find_one(
                    {"user_id": caller.id}
                )
                if therapist_profile and session.get("therapist_id") == therapist_profile.get("id"):
                    therapist_owns = True

            if not is_staff and not (client_owns or therapist_owns):
                raise ForbiddenException(
                    message="You cannot reference a session that does not belong to you.",
                    code=ErrorCode.SUPPORT_TICKET_REFERENCE_FORBIDDEN,
                )

    async def create_ticket(
        self, caller: UserInDB, req: CreateSupportTicketRequest
    ) -> SupportTicketResponse:
        """Create a new support ticket with reference ownership verification."""
        await self._validate_references(caller, req)

        # Non-staff users cannot arbitrarily set priority to URGENT
        priority = req.priority
        if priority == SupportPriority.URGENT and not self._is_staff_or_admin(caller):
            priority = SupportPriority.HIGH

        ticket_number = await self.support_repo.get_next_ticket_number()
        requester_role = (
            "therapist" if UserRole.THERAPIST in caller.roles else "user"
        )
        now = utc_now()
        ticket_id = str(uuid.uuid4())

        ticket = SupportTicketInDB(
            id=ticket_id,
            ticket_number=ticket_number,
            requester_id=caller.id,
            requester_role=requester_role,
            assigned_to=None,
            category=req.category,
            priority=priority,
            status=SupportTicketStatus.OPEN,
            subject=req.subject.strip(),
            description=req.description.strip(),
            booking_id=req.booking_id,
            payment_id=req.payment_id,
            package_id=req.package_id,
            session_id=req.session_id,
            attachments=req.attachments,
            created_at=now,
            updated_at=now,
        )
        saved_ticket = await self.support_repo.create_ticket(ticket)

        # Automatically insert opening message in conversation thread
        sender_name = (
            f"{caller.first_name} {caller.last_name or ''}".strip()
            or "Client"
        )
        opening_message = SupportMessageInDB(
            id=str(uuid.uuid4()),
            ticket_id=ticket_id,
            sender_id=caller.id,
            sender_role=requester_role,
            sender_display_name=sender_name,
            message=req.description.strip(),
            attachments=req.attachments,
            is_internal_note=False,
            created_at=now,
            updated_at=now,
        )
        await self.support_repo.create_message(opening_message)

        return SupportTicketResponse.from_db(saved_ticket)

    async def get_ticket_with_messages(
        self, caller: UserInDB, ticket_id: str
    ) -> tuple[SupportTicketResponse, list[SupportMessageResponse]]:
        """Fetch ticket and conversation history with IDOR boundary protection."""
        ticket = await self.support_repo.get_ticket_by_id(ticket_id)
        if not ticket:
            raise NotFoundException(
                message=f"Support ticket '{ticket_id}' not found.",
                code=ErrorCode.SUPPORT_TICKET_NOT_FOUND,
            )

        is_staff = self._is_staff_or_admin(caller)
        if not is_staff and ticket.requester_id != caller.id:
            raise ForbiddenException(
                message="You do not have permission to view this support ticket.",
                code=ErrorCode.SUPPORT_TICKET_FORBIDDEN,
            )

        # Retrieve messages (strictly omitting internal staff notes for clients)
        messages = await self.support_repo.list_messages_for_ticket(
            ticket_id=ticket_id, include_internal=is_staff
        )
        return (
            SupportTicketResponse.from_db(ticket),
            [SupportMessageResponse.from_db(m) for m in messages],
        )

    async def list_my_tickets(
        self,
        caller: UserInDB,
        status: SupportTicketStatus | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[SupportTicketResponse], int]:
        """List tickets created by the authenticated user."""
        tickets, total = await self.support_repo.list_tickets_for_requester(
            requester_id=caller.id, status=status, page=page, limit=limit
        )
        return [SupportTicketResponse.from_db(t) for t in tickets], total

    async def create_message(
        self,
        caller: UserInDB,
        ticket_id: str,
        req: CreateSupportMessageRequest,
    ) -> SupportMessageResponse:
        """Append a reply or internal note to a support conversation."""
        ticket = await self.support_repo.get_ticket_by_id(ticket_id)
        if not ticket:
            raise NotFoundException(
                message=f"Support ticket '{ticket_id}' not found.",
                code=ErrorCode.SUPPORT_TICKET_NOT_FOUND,
            )

        is_staff = self._is_staff_or_admin(caller)
        if not is_staff and ticket.requester_id != caller.id:
            raise ForbiddenException(
                message="You do not have permission to reply to this ticket.",
                code=ErrorCode.SUPPORT_MESSAGE_FORBIDDEN,
            )

        if ticket.status == SupportTicketStatus.CLOSED:
            raise BadRequestException(
                message="Cannot add messages to a closed support ticket.",
                code=ErrorCode.SUPPORT_TICKET_INVALID_STATE,
            )

        # Clients cannot write internal staff notes
        is_internal = req.is_internal_note if is_staff else False

        # Determine sender role & display name
        if is_staff:
            sender_role = "staff"
            sender_display_name = (
                f"{caller.first_name} (Support)" if caller.first_name else "Oppam Support"
            )
        else:
            sender_role = "therapist" if UserRole.THERAPIST in caller.roles else "user"
            sender_display_name = (
                f"{caller.first_name} {caller.last_name or ''}".strip()
                or "Client"
            )

        message = SupportMessageInDB(
            id=str(uuid.uuid4()),
            ticket_id=ticket.id,
            sender_id=caller.id,
            sender_role=sender_role,
            sender_display_name=sender_display_name,
            message=req.message.strip(),
            attachments=req.attachments,
            is_internal_note=is_internal,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        saved = await self.support_repo.create_message(message)

        # Automatic status transitions based on who replied
        if not is_internal:
            if not is_staff:
                # Client replied: reopen if resolved, or set in_progress if waiting
                if ticket.status in [
                    SupportTicketStatus.WAITING_FOR_USER,
                    SupportTicketStatus.RESOLVED,
                ]:
                    await self.support_repo.update_ticket_status(
                        ticket_id=ticket.id,
                        status=SupportTicketStatus.IN_PROGRESS,
                    )
            else:
                # Staff replied: mark in_progress if was open
                if ticket.status == SupportTicketStatus.OPEN:
                    await self.support_repo.update_ticket_status(
                        ticket_id=ticket.id,
                        status=SupportTicketStatus.IN_PROGRESS,
                    )

        return SupportMessageResponse.from_db(saved)

    async def close_ticket(
        self, caller: UserInDB, ticket_id: str
    ) -> SupportTicketResponse:
        """Close an open ticket (allowed for ticket owner or staff)."""
        ticket = await self.support_repo.get_ticket_by_id(ticket_id)
        if not ticket:
            raise NotFoundException(
                message=f"Support ticket '{ticket_id}' not found.",
                code=ErrorCode.SUPPORT_TICKET_NOT_FOUND,
            )

        is_staff = self._is_staff_or_admin(caller)
        if not is_staff and ticket.requester_id != caller.id:
            raise ForbiddenException(
                message="You do not have permission to close this ticket.",
                code=ErrorCode.SUPPORT_TICKET_FORBIDDEN,
            )

        if ticket.status == SupportTicketStatus.CLOSED:
            return SupportTicketResponse.from_db(ticket)

        now = utc_now()
        updated = await self.support_repo.update_ticket_status(
            ticket_id=ticket.id,
            status=SupportTicketStatus.CLOSED,
            closed_at=now,
        )
        assert updated is not None
        return SupportTicketResponse.from_db(updated)

    async def list_all_tickets(
        self,
        caller: UserInDB,
        status: SupportTicketStatus | None = None,
        category: SupportCategory | None = None,
        assigned_to: str | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[SupportTicketResponse], int]:
        """List all platform tickets (Staff/Admin only)."""
        if not self._is_staff_or_admin(caller):
            raise ForbiddenException(
                message="Staff privileges required.",
                code=ErrorCode.FORBIDDEN,
            )
        tickets, total = await self.support_repo.list_all_tickets(
            status=status,
            category=category,
            assigned_to=assigned_to,
            page=page,
            limit=limit,
        )
        return [SupportTicketResponse.from_db(t) for t in tickets], total

    async def assign_ticket(
        self, caller: UserInDB, ticket_id: str, staff_id: str
    ) -> SupportTicketResponse:
        """Assign ticket to a staff member (Staff/Admin only)."""
        if not self._is_staff_or_admin(caller):
            raise ForbiddenException(
                message="Staff privileges required.",
                code=ErrorCode.FORBIDDEN,
            )

        updated = await self.support_repo.assign_ticket(
            ticket_id=ticket_id, staff_id=staff_id
        )
        if not updated:
            raise NotFoundException(
                message=f"Support ticket '{ticket_id}' not found.",
                code=ErrorCode.SUPPORT_TICKET_NOT_FOUND,
            )
        return SupportTicketResponse.from_db(updated)

    async def update_ticket_status(
        self,
        caller: UserInDB,
        ticket_id: str,
        status: SupportTicketStatus,
    ) -> SupportTicketResponse:
        """Update ticket lifecycle status (Staff/Admin only)."""
        if not self._is_staff_or_admin(caller):
            raise ForbiddenException(
                message="Staff privileges required.",
                code=ErrorCode.FORBIDDEN,
            )

        resolved_at = utc_now() if status == SupportTicketStatus.RESOLVED else None
        closed_at = utc_now() if status == SupportTicketStatus.CLOSED else None

        updated = await self.support_repo.update_ticket_status(
            ticket_id=ticket_id,
            status=status,
            resolved_at=resolved_at,
            closed_at=closed_at,
        )
        if not updated:
            raise NotFoundException(
                message=f"Support ticket '{ticket_id}' not found.",
                code=ErrorCode.SUPPORT_TICKET_NOT_FOUND,
            )
        return SupportTicketResponse.from_db(updated)
