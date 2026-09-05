"""Presentation controller layer for Support module."""

from app.common.responses.api_response import ApiResponse, success_response
from app.modules.support.support_constants import (
    SupportCategory,
    SupportTicketStatus,
)
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
from app.modules.user.user_model import UserInDB


class SupportController:
    """Controller handling HTTP serialization and responses for Support endpoints."""

    def __init__(self, service: SupportService) -> None:
        self.service = service

    async def create_ticket(
        self, caller: UserInDB, req: CreateSupportTicketRequest
    ) -> ApiResponse[SupportTicketResponse]:
        res = await self.service.create_ticket(caller=caller, req=req)
        return success_response(
            data=res, message="Support ticket created successfully"
        )

    async def get_ticket(
        self, caller: UserInDB, ticket_id: str
    ) -> ApiResponse[SupportTicketDetailResponse]:
        ticket, messages = await self.service.get_ticket_with_messages(
            caller=caller, ticket_id=ticket_id
        )
        return success_response(
            data=SupportTicketDetailResponse(ticket=ticket, messages=messages)
        )

    async def list_my_tickets(
        self,
        caller: UserInDB,
        status: SupportTicketStatus | None,
        page: int,
        limit: int,
    ) -> ApiResponse[list[SupportTicketResponse]]:
        items, total = await self.service.list_my_tickets(
            caller=caller, status=status, page=page, limit=limit
        )
        return success_response(
            data=items,
            meta={
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit if total > 0 else 0,
            },
        )

    async def create_message(
        self,
        caller: UserInDB,
        ticket_id: str,
        req: CreateSupportMessageRequest,
    ) -> ApiResponse[SupportMessageResponse]:
        res = await self.service.create_message(
            caller=caller, ticket_id=ticket_id, req=req
        )
        return success_response(
            data=res, message="Message sent successfully"
        )

    async def close_ticket(
        self, caller: UserInDB, ticket_id: str
    ) -> ApiResponse[SupportTicketResponse]:
        res = await self.service.close_ticket(caller=caller, ticket_id=ticket_id)
        return success_response(
            data=res, message="Support ticket closed successfully"
        )

    async def list_all_tickets(
        self,
        caller: UserInDB,
        status: SupportTicketStatus | None,
        category: SupportCategory | None,
        assigned_to: str | None,
        page: int,
        limit: int,
    ) -> ApiResponse[list[SupportTicketResponse]]:
        items, total = await self.service.list_all_tickets(
            caller=caller,
            status=status,
            category=category,
            assigned_to=assigned_to,
            page=page,
            limit=limit,
        )
        return success_response(
            data=items,
            meta={
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit if total > 0 else 0,
            },
        )

    async def assign_ticket(
        self, caller: UserInDB, ticket_id: str, req: AssignTicketRequest
    ) -> ApiResponse[SupportTicketResponse]:
        res = await self.service.assign_ticket(
            caller=caller, ticket_id=ticket_id, staff_id=req.staff_id
        )
        return success_response(
            data=res, message="Ticket assigned successfully"
        )

    async def update_status(
        self, caller: UserInDB, ticket_id: str, req: UpdateTicketStatusRequest
    ) -> ApiResponse[SupportTicketResponse]:
        res = await self.service.update_ticket_status(
            caller=caller, ticket_id=ticket_id, status=req.status
        )
        return success_response(
            data=res, message="Ticket status updated successfully"
        )
