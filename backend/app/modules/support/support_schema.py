"""Pydantic schemas for Support module."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.modules.support.support_constants import (
    SupportCategory,
    SupportPriority,
    SupportTicketStatus,
)
from app.modules.support.support_model import (
    SupportAttachment,
    SupportMessageInDB,
    SupportTicketInDB,
)


class CreateSupportTicketRequest(BaseModel):
    """Payload to open a new support inquiry."""

    category: SupportCategory
    subject: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=5, max_length=5000)
    priority: SupportPriority = Field(default=SupportPriority.NORMAL)

    # Optional references
    booking_id: str | None = None
    payment_id: str | None = None
    package_id: str | None = None
    session_id: str | None = None

    attachments: list[SupportAttachment] = Field(default_factory=list)


class SupportTicketResponse(BaseModel):
    """Detailed representation of a support ticket."""

    id: str
    ticket_number: str
    requester_id: str
    requester_role: str
    assigned_to: str | None
    category: SupportCategory
    priority: SupportPriority
    status: SupportTicketStatus
    subject: str
    description: str

    booking_id: str | None
    payment_id: str | None
    package_id: str | None
    session_id: str | None

    attachments: list[SupportAttachment]
    created_at: datetime
    updated_at: datetime
    resolved_at: datetime | None
    closed_at: datetime | None

    @classmethod
    def from_db(cls, doc: SupportTicketInDB) -> "SupportTicketResponse":
        return cls(
            id=doc.id,
            ticket_number=doc.ticket_number,
            requester_id=doc.requester_id,
            requester_role=doc.requester_role,
            assigned_to=doc.assigned_to,
            category=doc.category,
            priority=doc.priority,
            status=doc.status,
            subject=doc.subject,
            description=doc.description,
            booking_id=doc.booking_id,
            payment_id=doc.payment_id,
            package_id=doc.package_id,
            session_id=doc.session_id,
            attachments=doc.attachments,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
            resolved_at=doc.resolved_at,
            closed_at=doc.closed_at,
        )


class CreateSupportMessageRequest(BaseModel):
    """Payload to append a reply or note to an existing ticket."""

    message: str = Field(min_length=1, max_length=5000)
    attachments: list[SupportAttachment] = Field(default_factory=list)
    is_internal_note: bool = Field(default=False)


class SupportMessageResponse(BaseModel):
    """Conversation message representation."""

    id: str
    ticket_id: str
    sender_id: str
    sender_role: str
    sender_display_name: str
    message: str
    attachments: list[SupportAttachment]
    is_internal_note: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_db(cls, doc: SupportMessageInDB) -> "SupportMessageResponse":
        return cls(
            id=doc.id,
            ticket_id=doc.ticket_id,
            sender_id=doc.sender_id,
            sender_role=doc.sender_role,
            sender_display_name=doc.sender_display_name,
            message=doc.message,
            attachments=doc.attachments,
            is_internal_note=doc.is_internal_note,
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )


class AssignTicketRequest(BaseModel):
    """Payload to assign a ticket to a staff member."""

    staff_id: str = Field(description="UUID of staff user")


class UpdateTicketStatusRequest(BaseModel):
    """Payload to update ticket lifecycle status."""

    status: SupportTicketStatus


class SupportTicketDetailResponse(BaseModel):
    """Combined ticket details and conversation messages."""

    ticket: SupportTicketResponse
    messages: list[SupportMessageResponse]
