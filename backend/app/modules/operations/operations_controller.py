"""Controller handling HTTP serialization and responses for Operations."""

from typing import Any

from app.common.responses.api_response import ApiResponse, success_response
from app.modules.operations.operations_constants import AuditAction, LeadStatus, Permission
from app.modules.operations.operations_schema import (
    AdminDashboardMetricsResponse,
    AuditLogResponse,
    LeadAssignRequest,
    LeadCreateRequest,
    LeadResponse,
    LeadUpdateRequest,
    OperationUserDetailResponse,
    UpdateUserRolesRequest,
    UpdateUserStatusRequest,
)
from app.modules.operations.operations_service import OperationsService
from app.modules.therapist.therapist_schema import (
    AdminUpdateTherapistVerificationRequest,
    TherapistDetailResponse,
    UpdateTherapistRequest,
)
from app.modules.user.user_constants import UserRole, UserStatus
from app.modules.user.user_model import UserInDB


class OperationsController:
    """Controller mediating FastAPI routes and OperationsService."""

    def __init__(self, service: OperationsService) -> None:
        self.service = service

    async def get_dashboard_metrics(
        self, caller: UserInDB
    ) -> ApiResponse[AdminDashboardMetricsResponse]:
        """Fetch dashboard metrics."""
        res = await self.service.get_dashboard_metrics(caller)
        return success_response(data=res)

    async def list_users(
        self,
        caller: UserInDB,
        role: UserRole | None,
        status: UserStatus | None,
        search: str | None,
        page: int,
        limit: int,
    ) -> ApiResponse[list[OperationUserDetailResponse]]:
        """List platform users."""
        users, total = await self.service.list_users(
            caller=caller, role=role, status=status, search=search, page=page, limit=limit
        )
        return success_response(
            data=users,
            meta={
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit if total > 0 else 0,
            },
        )

    async def get_user_detail(
        self, caller: UserInDB, user_id: str
    ) -> ApiResponse[OperationUserDetailResponse]:
        """Get user detail."""
        res = await self.service.get_user_detail(caller=caller, user_id=user_id)
        return success_response(data=res)

    async def update_user_status(
        self,
        caller: UserInDB,
        user_id: str,
        req: UpdateUserStatusRequest,
        request_id: str | None,
    ) -> ApiResponse[OperationUserDetailResponse]:
        """Update user account status."""
        res = await self.service.update_user_status(
            caller=caller, user_id=user_id, req=req, request_id=request_id
        )
        return success_response(data=res, message="User status updated successfully")

    async def update_user_roles(
        self,
        caller: UserInDB,
        user_id: str,
        req: UpdateUserRolesRequest,
        request_id: str | None,
    ) -> ApiResponse[OperationUserDetailResponse]:
        """Update user roles (Super Admin only)."""
        res = await self.service.update_user_roles(
            caller=caller, user_id=user_id, req=req, request_id=request_id
        )
        return success_response(data=res, message="User roles updated successfully")

    async def list_therapists(
        self,
        caller: UserInDB,
        status: str | None,
        verification_status: str | None,
        page: int,
        limit: int,
    ) -> ApiResponse[list[TherapistDetailResponse]]:
        """List therapists for operations."""
        therapists, total = await self.service.list_therapists_operational(
            caller=caller,
            status=status,
            verification_status=verification_status,
            page=page,
            limit=limit,
        )
        return success_response(
            data=therapists,
            meta={
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit if total > 0 else 0,
            },
        )

    async def verify_therapist(
        self,
        caller: UserInDB,
        therapist_id: str,
        req: AdminUpdateTherapistVerificationRequest,
        request_id: str | None,
    ) -> ApiResponse[TherapistDetailResponse]:
        """Verify therapist."""
        res = await self.service.verify_therapist(
            caller=caller, therapist_id=therapist_id, req=req, request_id=request_id
        )
        return success_response(data=res, message="Therapist verification updated")

    async def update_therapist_status(
        self,
        caller: UserInDB,
        therapist_id: str,
        req: UpdateTherapistRequest,
        request_id: str | None,
    ) -> ApiResponse[TherapistDetailResponse]:
        """Update therapist operational status."""
        res = await self.service.update_therapist_operational_status(
            caller=caller, therapist_id=therapist_id, req=req, request_id=request_id
        )
        return success_response(data=res, message="Therapist status updated")

    async def list_bookings(
        self,
        caller: UserInDB,
        status: str | None,
        therapist_id: str | None,
        client_id: str | None,
        page: int,
        limit: int,
    ) -> ApiResponse[list[dict[str, Any]]]:
        """List bookings operationally."""
        bookings, total = await self.service.list_bookings_operational(
            caller=caller,
            status=status,
            therapist_id=therapist_id,
            client_id=client_id,
            page=page,
            limit=limit,
        )
        return success_response(
            data=[b.model_dump() for b in bookings],
            meta={
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit if total > 0 else 0,
            },
        )

    async def list_payments(
        self,
        caller: UserInDB,
        status: str | None,
        provider: str | None,
        user_id: str | None,
        page: int,
        limit: int,
    ) -> ApiResponse[list[dict[str, Any]]]:
        """List payments operationally."""
        payments, total = await self.service.list_payments_operational(
            caller=caller,
            status=status,
            provider=provider,
            user_id=user_id,
            page=page,
            limit=limit,
        )
        return success_response(
            data=[p.model_dump() for p in payments],
            meta={
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit if total > 0 else 0,
            },
        )

    # --- Lead Management ---

    async def create_lead(
        self, caller: UserInDB, req: LeadCreateRequest, request_id: str | None
    ) -> ApiResponse[LeadResponse]:
        """Create lead."""
        res = await self.service.create_lead(caller=caller, req=req, request_id=request_id)
        return success_response(data=res, message="Lead created successfully")

    async def list_leads(
        self,
        caller: UserInDB,
        status: LeadStatus | None,
        assigned_to: str | None,
        search: str | None,
        page: int,
        limit: int,
    ) -> ApiResponse[list[LeadResponse]]:
        """List leads."""
        leads, total = await self.service.list_leads(
            caller=caller,
            status=status,
            assigned_to=assigned_to,
            search=search,
            page=page,
            limit=limit,
        )
        return success_response(
            data=leads,
            meta={
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit if total > 0 else 0,
            },
        )

    async def get_lead_by_id(
        self, caller: UserInDB, lead_id: str
    ) -> ApiResponse[LeadResponse]:
        """Get lead by ID."""
        res = await self.service.get_lead_by_id(caller=caller, lead_id=lead_id)
        return success_response(data=res)

    async def update_lead(
        self,
        caller: UserInDB,
        lead_id: str,
        req: LeadUpdateRequest,
        request_id: str | None,
    ) -> ApiResponse[LeadResponse]:
        """Update lead."""
        res = await self.service.update_lead(
            caller=caller, lead_id=lead_id, req=req, request_id=request_id
        )
        return success_response(data=res, message="Lead updated successfully")

    async def assign_lead(
        self,
        caller: UserInDB,
        lead_id: str,
        req: LeadAssignRequest,
        request_id: str | None,
    ) -> ApiResponse[LeadResponse]:
        """Assign lead."""
        res = await self.service.assign_lead(
            caller=caller, lead_id=lead_id, req=req, request_id=request_id
        )
        return success_response(data=res, message="Lead assigned successfully")

    async def convert_lead_to_user(
        self,
        caller: UserInDB,
        lead_id: str,
        user_id: str,
        request_id: str | None,
    ) -> ApiResponse[LeadResponse]:
        """Convert lead to user."""
        res = await self.service.convert_lead_to_user(
            caller=caller, lead_id=lead_id, user_id=user_id, request_id=request_id
        )
        return success_response(data=res, message="Lead converted to registered user")

    # --- Audit Logs ---

    async def list_audit_logs(
        self,
        caller: UserInDB,
        actor_id: str | None,
        resource_type: str | None,
        resource_id: str | None,
        action: AuditAction | None,
        page: int,
        limit: int,
    ) -> ApiResponse[list[AuditLogResponse]]:
        """List audit records."""
        self.service.require_permission(caller, Permission.AUDIT_READ)
        logs, total = await self.service.ops_repo.list_audit_logs(
            actor_id=actor_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            page=page,
            limit=limit,
        )
        return success_response(
            data=[AuditLogResponse.from_db(log) for log in logs],
            meta={
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit if total > 0 else 0,
            },
        )
