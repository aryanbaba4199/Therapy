"""MongoDB database models for the Operations, Lead, and Audit domains."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.common.utils.datetime_utils import utc_now
from app.modules.operations.operations_constants import AuditAction, LeadSource, LeadStatus


class AuditLogInDB(BaseModel):
    """Append-only audit trail record for privileged operations."""

    id: str
    actor_id: str
    actor_role: str
    action: AuditAction
    resource_type: str
    resource_id: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    request_id: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class LeadInDB(BaseModel):
    """Prospective client lead for first responders and operational triage."""

    id: str
    name: str
    phone: str
    email: str | None = None
    source: LeadSource = LeadSource.WEBSITE
    status: LeadStatus = LeadStatus.NEW
    assigned_to: str | None = None
    notes: str | None = None
    last_contacted_at: datetime | None = None
    next_follow_up_at: datetime | None = None
    converted_user_id: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
