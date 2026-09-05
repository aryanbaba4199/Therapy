"""Request and response schemas for Operations, Admin, and First Responder."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.modules.operations.operations_constants import AuditAction, LeadSource, LeadStatus
from app.modules.operations.operations_model import AuditLogInDB, LeadInDB
from app.modules.user.user_constants import UserRole, UserStatus
from app.modules.user.user_model import UserInDB


class AdminDashboardMetricsResponse(BaseModel):
    """High-level operational metrics aggregated from MongoDB collections."""

    today_bookings: int
    upcoming_sessions: int
    completed_sessions: int
    active_therapists: int
    pending_verification_therapists: int
    pending_support_tickets: int
    failed_payments_count: int
    total_revenue_minor: int
    new_leads_count: int


class UpdateUserStatusRequest(BaseModel):
    """Admin request to change a user's operational status."""

    status: UserStatus
    reason: str = Field(min_length=3, max_length=500)


class UpdateUserRolesRequest(BaseModel):
    """Super Admin request to modify a user's roles."""

    roles: list[UserRole] = Field(min_length=1)
    reason: str = Field(min_length=3, max_length=500)


class LeadCreateRequest(BaseModel):
    """Create a new prospective client lead."""

    name: str = Field(min_length=2, max_length=100)
    phone: str = Field(min_length=8, max_length=20)
    email: str | None = None
    source: LeadSource = LeadSource.WEBSITE
    notes: str | None = Field(default=None, max_length=1000)
    next_follow_up_at: datetime | None = None


class LeadUpdateRequest(BaseModel):
    """Update lead details, notes, or follow-up schedule."""

    name: str | None = Field(default=None, min_length=2, max_length=100)
    phone: str | None = Field(default=None, min_length=8, max_length=20)
    email: str | None = None
    source: LeadSource | None = None
    status: LeadStatus | None = None
    notes: str | None = Field(default=None, max_length=1000)
    next_follow_up_at: datetime | None = None


class LeadAssignRequest(BaseModel):
    """Assign or reassign a lead to a staff member or first responder."""

    assigned_to: str
    notes: str | None = None


class LeadResponse(BaseModel):
    """Serialized lead representation."""

    id: str
    name: str
    phone: str
    email: str | None
    source: LeadSource
    status: LeadStatus
    assigned_to: str | None
    notes: str | None
    last_contacted_at: datetime | None
    next_follow_up_at: datetime | None
    converted_user_id: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_db(cls, lead: LeadInDB) -> "LeadResponse":
        return cls(
            id=lead.id,
            name=lead.name,
            phone=lead.phone,
            email=lead.email,
            source=lead.source,
            status=lead.status,
            assigned_to=lead.assigned_to,
            notes=lead.notes,
            last_contacted_at=lead.last_contacted_at,
            next_follow_up_at=lead.next_follow_up_at,
            converted_user_id=lead.converted_user_id,
            created_at=lead.created_at,
            updated_at=lead.updated_at,
        )


class AuditLogResponse(BaseModel):
    """Serialized audit log representation."""

    id: str
    actor_id: str
    actor_role: str
    action: AuditAction
    resource_type: str
    resource_id: str
    metadata: dict[str, Any]
    request_id: str | None
    created_at: datetime

    @classmethod
    def from_db(cls, log: AuditLogInDB) -> "AuditLogResponse":
        return cls(
            id=log.id,
            actor_id=log.actor_id,
            actor_role=log.actor_role,
            action=log.action,
            resource_type=log.resource_type,
            resource_id=log.resource_id,
            metadata=log.metadata,
            request_id=log.request_id,
            created_at=log.created_at,
        )


class OperationUserDetailResponse(BaseModel):
    """Detailed user view for admin operations."""

    id: str
    first_name: str
    last_name: str
    email: str | None
    phone: str | None
    roles: list[UserRole]
    status: UserStatus
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None

    @classmethod
    def from_db(cls, user: UserInDB) -> "OperationUserDetailResponse":
        return cls(
            id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            email=user.email,
            phone=user.phone,
            roles=user.roles,
            status=user.status,
            is_verified=user.is_verified,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login_at=user.last_login_at,
        )
