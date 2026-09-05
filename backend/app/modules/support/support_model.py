"""MongoDB database persistence models for Support Tickets and Messages."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.common.utils.datetime_utils import ensure_utc, utc_now
from app.modules.support.support_constants import (
    SupportCategory,
    SupportPriority,
    SupportTicketStatus,
)


class SupportAttachment(BaseModel):
    """Reference metadata for uploaded ticket attachments (no raw binary in MongoDB)."""

    filename: str = Field(description="Original filename")
    file_url: str = Field(description="Secured storage URL / object key")
    mime_type: str = Field(default="application/octet-stream", description="MIME content type")
    size_bytes: int = Field(ge=0, description="File size in bytes")


class SupportTicketInDB(BaseModel):
    """Database model for a customer support ticket stored in `support_tickets`."""

    id: str = Field(description="Unique support ticket UUID")
    ticket_number: str = Field(description="Human-friendly reference identifier e.g. TCK-10023")
    requester_id: str = Field(description="UUID of user or therapist who created ticket")
    requester_role: str = Field(default="user", description="Role of requester")
    assigned_to: str | None = Field(default=None, description="UUID of assigned staff member")

    category: SupportCategory = Field(description="Inquiry category")
    priority: SupportPriority = Field(default=SupportPriority.NORMAL, description="Urgency level")
    status: SupportTicketStatus = Field(default=SupportTicketStatus.OPEN, description="Current lifecycle status")

    subject: str = Field(max_length=200, description="Brief subject of inquiry")
    description: str = Field(max_length=5000, description="Detailed problem statement")

    # Optional foreign domain references (validated strictly against IDOR)
    booking_id: str | None = Field(default=None, description="Referenced booking UUID")
    payment_id: str | None = Field(default=None, description="Referenced payment UUID")
    package_id: str | None = Field(default=None, description="Referenced package UUID")
    session_id: str | None = Field(default=None, description="Referenced session UUID")

    attachments: list[SupportAttachment] = Field(default_factory=list)

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    resolved_at: datetime | None = Field(default=None)
    closed_at: datetime | None = Field(default=None)

    @field_validator(
        "created_at", "updated_at", "resolved_at", "closed_at", mode="after"
    )
    @classmethod
    def ensure_tz(cls, v: datetime | None) -> datetime | None:
        return ensure_utc(v) if v is not None else None

    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        d = super().model_dump(*args, **kwargs)
        for key in ["created_at", "updated_at", "resolved_at", "closed_at"]:
            if key in d and isinstance(d[key], datetime):
                d[key] = ensure_utc(d[key])
        return d


class SupportMessageInDB(BaseModel):
    """Database model for conversation messages in `support_messages` collection."""

    id: str = Field(description="Unique message UUID")
    ticket_id: str = Field(description="Associated ticket UUID")
    sender_id: str = Field(description="User UUID of message author")
    sender_role: str = Field(description="Role of sender at time of message")
    sender_display_name: str = Field(description="Author display name")

    message: str = Field(max_length=5000, description="Conversation content")
    attachments: list[SupportAttachment] = Field(default_factory=list)
    is_internal_note: bool = Field(default=False, description="Private staff note invisible to client")

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("created_at", "updated_at", mode="after")
    @classmethod
    def ensure_tz(cls, v: datetime | None) -> datetime | None:
        return ensure_utc(v) if v is not None else None

    def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        d = super().model_dump(*args, **kwargs)
        for key in ["created_at", "updated_at"]:
            if key in d and isinstance(d[key], datetime):
                d[key] = ensure_utc(d[key])
        return d
