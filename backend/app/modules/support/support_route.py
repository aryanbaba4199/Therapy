"""FastAPI route registration for Support module."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.common.responses.api_response import ApiResponse
from app.modules.auth.auth_dependency import get_current_active_user, require_roles
from app.modules.support.support_constants import (
    SupportCategory,
    SupportTicketStatus,
)
from app.modules.support.support_controller import SupportController
from app.modules.support.support_dependency import get_support_service
from app.modules.support.support_schema import (
    AssignTicketRequest,
    CreateSupportMessageRequest,
    CreateSupportTicketRequest,
    SupportMessageResponse,
    SupportTicketDetailResponse,
    SupportTicketResponse,
    UpdateTicketStatusRequest,
)
from app.modules.support.support_service import SupportService
from app.modules.user.user_constants import UserRole
from app.modules.user.user_model import UserInDB

router = APIRouter(prefix="/support", tags=["Customer Support"])


def get_support_controller(
    service: SupportService = Depends(get_support_service),
) -> SupportController:
    return SupportController(service=service)


# --- Client / User Endpoints ---

@router.post(
    "/tickets",
    response_model=ApiResponse[SupportTicketResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new support ticket",
)
async def create_ticket(
    req: CreateSupportTicketRequest,
    caller: Annotated[UserInDB, Depends(get_current_active_user)],
    controller: Annotated[SupportController, Depends(get_support_controller)],
) -> ApiResponse[SupportTicketResponse]:
    return await controller.create_ticket(caller=caller, req=req)


@router.get(
    "/tickets",
    response_model=ApiResponse[list[SupportTicketResponse]],
    summary="List current user's support tickets",
)
async def list_my_tickets(
    caller: Annotated[UserInDB, Depends(get_current_active_user)],
    controller: Annotated[SupportController, Depends(get_support_controller)],
    status: SupportTicketStatus | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
) -> ApiResponse[list[SupportTicketResponse]]:
    return await controller.list_my_tickets(
        caller=caller, status=status, page=page, limit=limit
    )


@router.get(
    "/tickets/{ticket_id}",
    response_model=ApiResponse[SupportTicketDetailResponse],
    summary="Get support ticket details and conversation thread",
)
async def get_ticket(
    ticket_id: str,
    caller: Annotated[UserInDB, Depends(get_current_active_user)],
    controller: Annotated[SupportController, Depends(get_support_controller)],
) -> ApiResponse[SupportTicketDetailResponse]:
    return await controller.get_ticket(caller=caller, ticket_id=ticket_id)


@router.post(
    "/tickets/{ticket_id}/messages",
    response_model=ApiResponse[SupportMessageResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Reply to a support ticket",
)
async def create_message(
    ticket_id: str,
    req: CreateSupportMessageRequest,
    caller: Annotated[UserInDB, Depends(get_current_active_user)],
    controller: Annotated[SupportController, Depends(get_support_controller)],
) -> ApiResponse[SupportMessageResponse]:
    return await controller.create_message(
        caller=caller, ticket_id=ticket_id, req=req
    )


@router.post(
    "/tickets/{ticket_id}/close",
    response_model=ApiResponse[SupportTicketResponse],
    summary="Close support ticket",
)
async def close_ticket(
    ticket_id: str,
    caller: Annotated[UserInDB, Depends(get_current_active_user)],
    controller: Annotated[SupportController, Depends(get_support_controller)],
) -> ApiResponse[SupportTicketResponse]:
    return await controller.close_ticket(caller=caller, ticket_id=ticket_id)


# --- Staff Operations Endpoints ---

@router.get(
    "/staff/tickets",
    response_model=ApiResponse[list[SupportTicketResponse]],
    summary="List all support tickets across platform (Staff/Admin only)",
)
async def list_staff_tickets(
    caller: Annotated[
        UserInDB,
        Depends(
            require_roles(
                UserRole.STAFF, UserRole.ADMIN, UserRole.SUPER_ADMIN
            )
        ),
    ],
    controller: Annotated[SupportController, Depends(get_support_controller)],
    status: SupportTicketStatus | None = Query(None),
    category: SupportCategory | None = Query(None),
    assigned_to: str | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
) -> ApiResponse[list[SupportTicketResponse]]:
    return await controller.list_all_tickets(
        caller=caller,
        status=status,
        category=category,
        assigned_to=assigned_to,
        page=page,
        limit=limit,
    )


@router.post(
    "/staff/tickets/{ticket_id}/assign",
    response_model=ApiResponse[SupportTicketResponse],
    summary="Assign ticket to staff member (Staff/Admin only)",
)
async def assign_ticket(
    ticket_id: str,
    req: AssignTicketRequest,
    caller: Annotated[
        UserInDB,
        Depends(
            require_roles(
                UserRole.STAFF, UserRole.ADMIN, UserRole.SUPER_ADMIN
            )
        ),
    ],
    controller: Annotated[SupportController, Depends(get_support_controller)],
) -> ApiResponse[SupportTicketResponse]:
    return await controller.assign_ticket(
        caller=caller, ticket_id=ticket_id, req=req
    )


@router.patch(
    "/staff/tickets/{ticket_id}/status",
    response_model=ApiResponse[SupportTicketResponse],
    summary="Update support ticket status (Staff/Admin only)",
)
async def update_ticket_status(
    ticket_id: str,
    req: UpdateTicketStatusRequest,
    caller: Annotated[
        UserInDB,
        Depends(
            require_roles(
                UserRole.STAFF, UserRole.ADMIN, UserRole.SUPER_ADMIN
            )
        ),
    ],
    controller: Annotated[SupportController, Depends(get_support_controller)],
) -> ApiResponse[SupportTicketResponse]:
    return await controller.update_status(
        caller=caller, ticket_id=ticket_id, req=req
    )
