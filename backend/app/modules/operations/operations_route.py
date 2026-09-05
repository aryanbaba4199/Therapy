"""FastAPI route definitions for Operations, Admin, and First Responder platform."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from app.common.responses.api_response import ApiResponse
from app.middleware.request_id_middleware import get_request_id
from app.modules.operations.operations_constants import AuditAction, LeadStatus, Permission
from app.modules.operations.operations_controller import OperationsController
from app.modules.operations.operations_dependency import (
    get_operations_service,
    require_permission,
)
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


def get_operations_controller(
    service: Annotated[OperationsService, Depends(get_operations_service)],
) -> OperationsController:
    return OperationsController(service)


router = APIRouter(prefix="/operations", tags=["Operations & Administration"])


# --- Dashboard ---

@router.get(
    "/dashboard/metrics",
    response_model=ApiResponse[AdminDashboardMetricsResponse],
    summary="Get operational and administrative high-level metrics",
)
async def get_dashboard_metrics(
    caller: Annotated[UserInDB, Depends(require_permission(Permission.DASHBOARD_VIEW))],
    controller: Annotated[OperationsController, Depends(get_operations_controller)],
) -> ApiResponse[AdminDashboardMetricsResponse]:
    return await controller.get_dashboard_metrics(caller=caller)


# --- User Management ---

@router.get(
    "/users",
    response_model=ApiResponse[list[OperationUserDetailResponse]],
    summary="List platform users with operational filters",
)
async def list_users(
    caller: Annotated[UserInDB, Depends(require_permission(Permission.USERS_READ))],
    controller: Annotated[OperationsController, Depends(get_operations_controller)],
    role: UserRole | None = Query(default=None),
    status: UserStatus | None = Query(default=None),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
) -> ApiResponse[list[OperationUserDetailResponse]]:
    return await controller.list_users(
        caller=caller, role=role, status=status, search=search, page=page, limit=limit
    )


@router.get(
    "/users/{user_id}",
    response_model=ApiResponse[OperationUserDetailResponse],
    summary="Get operational details for a specific user",
)
async def get_user_detail(
    user_id: str,
    caller: Annotated[UserInDB, Depends(require_permission(Permission.USERS_READ))],
    controller: Annotated[OperationsController, Depends(get_operations_controller)],
) -> ApiResponse[OperationUserDetailResponse]:
    return await controller.get_user_detail(caller=caller, user_id=user_id)


@router.patch(
    "/users/{user_id}/status",
    response_model=ApiResponse[OperationUserDetailResponse],
    summary="Update user operational status (activate/suspend)",
)
async def update_user_status(
    user_id: str,
    req: UpdateUserStatusRequest,
    caller: Annotated[UserInDB, Depends(require_permission(Permission.USERS_SUSPEND))],
    controller: Annotated[OperationsController, Depends(get_operations_controller)],
    request_id: Annotated[str | None, Depends(get_request_id)] = None,
) -> ApiResponse[OperationUserDetailResponse]:
    return await controller.update_user_status(
        caller=caller, user_id=user_id, req=req, request_id=request_id
    )


@router.patch(
    "/users/{user_id}/roles",
    response_model=ApiResponse[OperationUserDetailResponse],
    summary="Update user roles (Super Admin only)",
)
async def update_user_roles(
    user_id: str,
    req: UpdateUserRolesRequest,
    caller: Annotated[UserInDB, Depends(require_permission(Permission.ROLES_MANAGE))],
    controller: Annotated[OperationsController, Depends(get_operations_controller)],
    request_id: Annotated[str | None, Depends(get_request_id)] = None,
) -> ApiResponse[OperationUserDetailResponse]:
    return await controller.update_user_roles(
        caller=caller, user_id=user_id, req=req, request_id=request_id
    )


# --- Therapist Operations ---

@router.get(
    "/therapists",
    response_model=ApiResponse[list[TherapistDetailResponse]],
    summary="List therapists with operational verification details",
)
async def list_therapists(
    caller: Annotated[UserInDB, Depends(require_permission(Permission.THERAPISTS_READ))],
    controller: Annotated[OperationsController, Depends(get_operations_controller)],
    status: str | None = Query(default=None),
    verification_status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
) -> ApiResponse[list[TherapistDetailResponse]]:
    return await controller.list_therapists(
        caller=caller,
        status=status,
        verification_status=verification_status,
        page=page,
        limit=limit,
    )


@router.patch(
    "/therapists/{therapist_id}/verify",
    response_model=ApiResponse[TherapistDetailResponse],
    summary="Verify or reject therapist credentials",
)
async def verify_therapist(
    therapist_id: str,
    req: AdminUpdateTherapistVerificationRequest,
    caller: Annotated[UserInDB, Depends(require_permission(Permission.THERAPISTS_VERIFY))],
    controller: Annotated[OperationsController, Depends(get_operations_controller)],
    request_id: Annotated[str | None, Depends(get_request_id)] = None,
) -> ApiResponse[TherapistDetailResponse]:
    return await controller.verify_therapist(
        caller=caller, therapist_id=therapist_id, req=req, request_id=request_id
    )


@router.patch(
    "/therapists/{therapist_id}/status",
    response_model=ApiResponse[TherapistDetailResponse],
    summary="Update therapist operational status (activate/inactivate/suspend)",
)
async def update_therapist_status(
    therapist_id: str,
    req: UpdateTherapistRequest,
    caller: Annotated[UserInDB, Depends(require_permission(Permission.THERAPISTS_MANAGE))],
    controller: Annotated[OperationsController, Depends(get_operations_controller)],
    request_id: Annotated[str | None, Depends(get_request_id)] = None,
) -> ApiResponse[TherapistDetailResponse]:
    return await controller.update_therapist_status(
        caller=caller, therapist_id=therapist_id, req=req, request_id=request_id
    )


# --- Booking & Payment Operations ---

@router.get(
    "/bookings",
    response_model=ApiResponse[list[dict[str, Any]]],
    summary="Operational bookings ledger with cross-cutting filters",
)
async def list_bookings(
    caller: Annotated[UserInDB, Depends(require_permission(Permission.BOOKINGS_READ))],
    controller: Annotated[OperationsController, Depends(get_operations_controller)],
    status: str | None = Query(default=None),
    therapist_id: str | None = Query(default=None),
    client_id: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
) -> ApiResponse[list[dict[str, Any]]]:
    return await controller.list_bookings(
        caller=caller,
        status=status,
        therapist_id=therapist_id,
        client_id=client_id,
        page=page,
        limit=limit,
    )


@router.get(
    "/payments",
    response_model=ApiResponse[list[dict[str, Any]]],
    summary="Operational payments ledger with failure visibility",
)
async def list_payments(
    caller: Annotated[UserInDB, Depends(require_permission(Permission.PAYMENTS_READ))],
    controller: Annotated[OperationsController, Depends(get_operations_controller)],
    status: str | None = Query(default=None),
    provider: str | None = Query(default=None),
    user_id: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
) -> ApiResponse[list[dict[str, Any]]]:
    return await controller.list_payments(
        caller=caller,
        status=status,
        provider=provider,
        user_id=user_id,
        page=page,
        limit=limit,
    )


# --- Lead & First Responder Management ---

@router.post(
    "/leads",
    response_model=ApiResponse[LeadResponse],
    summary="Create prospective client lead (First Responder/Staff)",
)
async def create_lead(
    req: LeadCreateRequest,
    caller: Annotated[UserInDB, Depends(require_permission(Permission.LEADS_MANAGE))],
    controller: Annotated[OperationsController, Depends(get_operations_controller)],
    request_id: Annotated[str | None, Depends(get_request_id)] = None,
) -> ApiResponse[LeadResponse]:
    return await controller.create_lead(caller=caller, req=req, request_id=request_id)


@router.get(
    "/leads",
    response_model=ApiResponse[list[LeadResponse]],
    summary="List prospective client leads with triage filters",
)
async def list_leads(
    caller: Annotated[UserInDB, Depends(require_permission(Permission.LEADS_READ))],
    controller: Annotated[OperationsController, Depends(get_operations_controller)],
    status: LeadStatus | None = Query(default=None),
    assigned_to: str | None = Query(default=None),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
) -> ApiResponse[list[LeadResponse]]:
    return await controller.list_leads(
        caller=caller,
        status=status,
        assigned_to=assigned_to,
        search=search,
        page=page,
        limit=limit,
    )


@router.get(
    "/leads/{lead_id}",
    response_model=ApiResponse[LeadResponse],
    summary="Get lead details",
)
async def get_lead_by_id(
    lead_id: str,
    caller: Annotated[UserInDB, Depends(require_permission(Permission.LEADS_READ))],
    controller: Annotated[OperationsController, Depends(get_operations_controller)],
) -> ApiResponse[LeadResponse]:
    return await controller.get_lead_by_id(caller=caller, lead_id=lead_id)


@router.patch(
    "/leads/{lead_id}",
    response_model=ApiResponse[LeadResponse],
    summary="Update lead details or status",
)
async def update_lead(
    lead_id: str,
    req: LeadUpdateRequest,
    caller: Annotated[UserInDB, Depends(require_permission(Permission.LEADS_MANAGE))],
    controller: Annotated[OperationsController, Depends(get_operations_controller)],
    request_id: Annotated[str | None, Depends(get_request_id)] = None,
) -> ApiResponse[LeadResponse]:
    return await controller.update_lead(
        caller=caller, lead_id=lead_id, req=req, request_id=request_id
    )


@router.post(
    "/leads/{lead_id}/assign",
    response_model=ApiResponse[LeadResponse],
    summary="Assign or reassign lead to a staff member or first responder",
)
async def assign_lead(
    lead_id: str,
    req: LeadAssignRequest,
    caller: Annotated[UserInDB, Depends(require_permission(Permission.LEADS_ASSIGN))],
    controller: Annotated[OperationsController, Depends(get_operations_controller)],
    request_id: Annotated[str | None, Depends(get_request_id)] = None,
) -> ApiResponse[LeadResponse]:
    return await controller.assign_lead(
        caller=caller, lead_id=lead_id, req=req, request_id=request_id
    )


@router.post(
    "/leads/{lead_id}/convert/{user_id}",
    response_model=ApiResponse[LeadResponse],
    summary="Convert lead to registered platform user",
)
async def convert_lead_to_user(
    lead_id: str,
    user_id: str,
    caller: Annotated[UserInDB, Depends(require_permission(Permission.LEADS_MANAGE))],
    controller: Annotated[OperationsController, Depends(get_operations_controller)],
    request_id: Annotated[str | None, Depends(get_request_id)] = None,
) -> ApiResponse[LeadResponse]:
    return await controller.convert_lead_to_user(
        caller=caller, lead_id=lead_id, user_id=user_id, request_id=request_id
    )


# --- Audit Logs ---

@router.get(
    "/audit-logs",
    response_model=ApiResponse[list[AuditLogResponse]],
    summary="Read-only chronological operational audit trail",
)
async def list_audit_logs(
    caller: Annotated[UserInDB, Depends(require_permission(Permission.AUDIT_READ))],
    controller: Annotated[OperationsController, Depends(get_operations_controller)],
    actor_id: str | None = Query(default=None),
    resource_type: str | None = Query(default=None),
    resource_id: str | None = Query(default=None),
    action: AuditAction | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
) -> ApiResponse[list[AuditLogResponse]]:
    return await controller.list_audit_logs(
        caller=caller,
        actor_id=actor_id,
        resource_type=resource_type,
        resource_id=resource_id,
        action=action,
        page=page,
        limit=limit,
    )
