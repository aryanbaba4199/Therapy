"""Support module exports."""

from app.modules.support.support_constants import (
    SupportCategory,
    SupportPriority,
    SupportTicketStatus,
)
from app.modules.support.support_controller import SupportController
from app.modules.support.support_dependency import (
    get_support_repository,
    get_support_service,
)
from app.modules.support.support_model import (
    SupportAttachment,
    SupportMessageInDB,
    SupportTicketInDB,
)
from app.modules.support.support_repository import SupportRepository
from app.modules.support.support_route import router as support_router
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

__all__ = [
    "SupportCategory",
    "SupportPriority",
    "SupportTicketStatus",
    "SupportAttachment",
    "SupportTicketInDB",
    "SupportMessageInDB",
    "SupportRepository",
    "SupportService",
    "SupportController",
    "support_router",
    "get_support_repository",
    "get_support_service",
    "CreateSupportTicketRequest",
    "SupportTicketResponse",
    "CreateSupportMessageRequest",
    "SupportMessageResponse",
    "SupportTicketDetailResponse",
    "AssignTicketRequest",
    "UpdateTicketStatusRequest",
]
