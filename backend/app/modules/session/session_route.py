"""FastAPI route registration for Session and Therapist Portal endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.common.responses.api_response import ApiResponse
from app.modules.auth.auth_dependency import get_current_active_user, require_roles
from app.modules.session.session_constants import SessionStatus
from app.modules.session.session_controller import SessionController
from app.modules.session.session_dependency import get_session_service
from app.modules.session.session_schema import (
    ClientSessionNoteResponse,
    ClientSessionResponse,
    CreateTherapyGoalRequest,
    RecordAttendanceRequest,
    SessionNoteResponse,
    SessionResponse,
    TherapistDashboardSummaryResponse,
    TherapyGoalResponse,
    UpdateTherapyGoalRequest,
    UpsertSessionNoteRequest,
)
from app.modules.session.session_service import SessionService
from app.modules.user.user_constants import UserRole
from app.modules.user.user_model import UserInDB

router = APIRouter(prefix="/sessions", tags=["Sessions"])
portal_router = APIRouter(prefix="/therapist/portal", tags=["Therapist Portal"])


def get_session_controller(
    service: SessionService = Depends(get_session_service),
) -> SessionController:
    return SessionController(service=service)


# --- Core Session Operations ---

@router.get(
    "/{session_id}",
    response_model=ApiResponse[SessionResponse],
    summary="Get session details (Therapist/Client/Admin)",
)
async def get_session(
    session_id: str,
    caller: Annotated[UserInDB, Depends(get_current_active_user)],
    controller: Annotated[SessionController, Depends(get_session_controller)],
) -> ApiResponse[SessionResponse]:
    return await controller.get_session(caller=caller, session_id=session_id)


@router.get(
    "/{session_id}/client-view",
    response_model=ApiResponse[ClientSessionResponse],
    summary="Get sanitized client view of session",
)
async def get_client_session_view(
    session_id: str,
    caller: Annotated[UserInDB, Depends(get_current_active_user)],
    controller: Annotated[SessionController, Depends(get_session_controller)],
) -> ApiResponse[ClientSessionResponse]:
    return await controller.get_client_session(caller=caller, session_id=session_id)


@router.post(
    "/{session_id}/start",
    response_model=ApiResponse[SessionResponse],
    summary="Start session (Therapist only)",
)
async def start_session(
    session_id: str,
    caller: Annotated[UserInDB, Depends(get_current_active_user)],
    controller: Annotated[SessionController, Depends(get_session_controller)],
) -> ApiResponse[SessionResponse]:
    return await controller.start_session(caller=caller, session_id=session_id)


@router.post(
    "/{session_id}/complete",
    response_model=ApiResponse[SessionResponse],
    summary="Complete session (Therapist only)",
)
async def complete_session(
    session_id: str,
    caller: Annotated[UserInDB, Depends(get_current_active_user)],
    controller: Annotated[SessionController, Depends(get_session_controller)],
) -> ApiResponse[SessionResponse]:
    return await controller.complete_session(caller=caller, session_id=session_id)


@router.post(
    "/{session_id}/attendance",
    response_model=ApiResponse[SessionResponse],
    summary="Record attendance (Therapist only)",
)
async def record_attendance(
    session_id: str,
    req: RecordAttendanceRequest,
    caller: Annotated[UserInDB, Depends(get_current_active_user)],
    controller: Annotated[SessionController, Depends(get_session_controller)],
) -> ApiResponse[SessionResponse]:
    return await controller.record_attendance(caller=caller, session_id=session_id, req=req)


# --- Clinical Notes Operations ---

@router.get(
    "/{session_id}/notes",
    response_model=ApiResponse[SessionNoteResponse],
    summary="Get clinical notes (Therapist only)",
)
async def get_session_note(
    session_id: str,
    caller: Annotated[UserInDB, Depends(require_roles(UserRole.THERAPIST, UserRole.ADMIN, UserRole.SUPER_ADMIN))],
    controller: Annotated[SessionController, Depends(get_session_controller)],
) -> ApiResponse[SessionNoteResponse]:
    return await controller.get_session_note(caller=caller, session_id=session_id)


@router.get(
    "/{session_id}/notes/client",
    response_model=ApiResponse[ClientSessionNoteResponse],
    summary="Get client-facing summary note (Client view)",
)
async def get_client_session_note(
    session_id: str,
    caller: Annotated[UserInDB, Depends(get_current_active_user)],
    controller: Annotated[SessionController, Depends(get_session_controller)],
) -> ApiResponse[ClientSessionNoteResponse]:
    return await controller.get_client_session_note(caller=caller, session_id=session_id)


@router.post(
    "/{session_id}/notes",
    response_model=ApiResponse[SessionNoteResponse],
    summary="Upsert clinical notes (Therapist only)",
)
async def upsert_session_note(
    session_id: str,
    req: UpsertSessionNoteRequest,
    caller: Annotated[UserInDB, Depends(require_roles(UserRole.THERAPIST, UserRole.ADMIN, UserRole.SUPER_ADMIN))],
    controller: Annotated[SessionController, Depends(get_session_controller)],
) -> ApiResponse[SessionNoteResponse]:
    return await controller.upsert_session_note(caller=caller, session_id=session_id, req=req)


# --- Therapy Goals Operations ---

@router.post(
    "/{session_id}/goals",
    response_model=ApiResponse[TherapyGoalResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create therapy goal (Therapist only)",
)
async def create_goal(
    session_id: str,
    req: CreateTherapyGoalRequest,
    caller: Annotated[UserInDB, Depends(require_roles(UserRole.THERAPIST, UserRole.ADMIN, UserRole.SUPER_ADMIN))],
    controller: Annotated[SessionController, Depends(get_session_controller)],
) -> ApiResponse[TherapyGoalResponse]:
    return await controller.create_goal(caller=caller, session_id=session_id, req=req)


@router.get(
    "/{session_id}/goals",
    response_model=ApiResponse[list[TherapyGoalResponse]],
    summary="List client therapy goals",
)
async def list_goals(
    session_id: str,
    caller: Annotated[UserInDB, Depends(get_current_active_user)],
    controller: Annotated[SessionController, Depends(get_session_controller)],
) -> ApiResponse[list[TherapyGoalResponse]]:
    return await controller.list_goals(caller=caller, session_id=session_id)


@router.patch(
    "/goals/{goal_id}",
    response_model=ApiResponse[TherapyGoalResponse],
    summary="Update therapy goal (Therapist only)",
)
async def update_goal(
    goal_id: str,
    req: UpdateTherapyGoalRequest,
    caller: Annotated[UserInDB, Depends(require_roles(UserRole.THERAPIST, UserRole.ADMIN, UserRole.SUPER_ADMIN))],
    controller: Annotated[SessionController, Depends(get_session_controller)],
) -> ApiResponse[TherapyGoalResponse]:
    return await controller.update_goal(caller=caller, goal_id=goal_id, req=req)


# --- Client Session View ---

@router.get(
    "/my/sessions",
    response_model=ApiResponse[list[ClientSessionResponse]],
    summary="List current client's sessions",
)
async def list_my_sessions(
    caller: Annotated[UserInDB, Depends(get_current_active_user)],
    controller: Annotated[SessionController, Depends(get_session_controller)],
    status: SessionStatus | None = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
) -> ApiResponse[list[ClientSessionResponse]]:
    return await controller.list_client_sessions(
        caller=caller, status=status, page=page, limit=limit
    )


# --- Therapist Portal Endpoints ---

@portal_router.get(
    "/dashboard",
    response_model=ApiResponse[TherapistDashboardSummaryResponse],
    summary="Get therapist dashboard agenda & statistics",
)
async def get_therapist_dashboard(
    caller: Annotated[UserInDB, Depends(require_roles(UserRole.THERAPIST, UserRole.ADMIN, UserRole.SUPER_ADMIN))],
    controller: Annotated[SessionController, Depends(get_session_controller)],
) -> ApiResponse[TherapistDashboardSummaryResponse]:
    return await controller.get_therapist_dashboard(caller=caller)


@portal_router.get(
    "/sessions",
    response_model=ApiResponse[list[SessionResponse]],
    summary="List therapist's sessions",
)
async def list_therapist_sessions(
    caller: Annotated[UserInDB, Depends(require_roles(UserRole.THERAPIST, UserRole.ADMIN, UserRole.SUPER_ADMIN))],
    controller: Annotated[SessionController, Depends(get_session_controller)],
    status: SessionStatus | None = Query(None),
    date_filter: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
) -> ApiResponse[list[SessionResponse]]:
    return await controller.list_therapist_sessions(
        caller=caller,
        status=status,
        date_filter=date_filter,
        page=page,
        limit=limit,
    )
