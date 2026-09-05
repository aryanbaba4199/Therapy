"""Presentation controller layer for Session endpoints."""

from app.common.responses.api_response import ApiResponse, success_response
from app.modules.session.session_constants import SessionStatus
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
from app.modules.user.user_model import UserInDB


class SessionController:
    """Controller handling HTTP serialization and response envelopes for sessions."""

    def __init__(self, service: SessionService) -> None:
        self.service = service

    async def get_session(
        self, caller: UserInDB, session_id: str
    ) -> ApiResponse[SessionResponse]:
        res = await self.service.get_session(session_id=session_id, caller=caller)
        return success_response(data=res)

    async def get_client_session(
        self, caller: UserInDB, session_id: str
    ) -> ApiResponse[ClientSessionResponse]:
        res = await self.service.get_client_session(session_id=session_id, caller=caller)
        return success_response(data=res)

    async def start_session(
        self, caller: UserInDB, session_id: str
    ) -> ApiResponse[SessionResponse]:
        res = await self.service.start_session(session_id=session_id, caller=caller)
        return success_response(data=res, message="Session started successfully")

    async def complete_session(
        self, caller: UserInDB, session_id: str
    ) -> ApiResponse[SessionResponse]:
        res = await self.service.complete_session(session_id=session_id, caller=caller)
        return success_response(data=res, message="Session completed successfully")

    async def record_attendance(
        self, caller: UserInDB, session_id: str, req: RecordAttendanceRequest
    ) -> ApiResponse[SessionResponse]:
        res = await self.service.record_attendance(session_id=session_id, caller=caller, req=req)
        return success_response(data=res, message="Attendance updated successfully")

    async def get_session_note(
        self, caller: UserInDB, session_id: str
    ) -> ApiResponse[SessionNoteResponse]:
        res = await self.service.get_session_note(session_id=session_id, caller=caller)
        return success_response(data=res)

    async def get_client_session_note(
        self, caller: UserInDB, session_id: str
    ) -> ApiResponse[ClientSessionNoteResponse]:
        res = await self.service.get_client_session_note(session_id=session_id, caller=caller)
        return success_response(data=res)

    async def upsert_session_note(
        self, caller: UserInDB, session_id: str, req: UpsertSessionNoteRequest
    ) -> ApiResponse[SessionNoteResponse]:
        res = await self.service.upsert_session_note(session_id=session_id, caller=caller, req=req)
        return success_response(data=res, message="Clinical notes saved successfully")

    async def create_goal(
        self, caller: UserInDB, session_id: str, req: CreateTherapyGoalRequest
    ) -> ApiResponse[TherapyGoalResponse]:
        res = await self.service.create_goal(session_id=session_id, caller=caller, req=req)
        return success_response(data=res, message="Therapy goal established successfully")

    async def list_goals(
        self, caller: UserInDB, session_id: str
    ) -> ApiResponse[list[TherapyGoalResponse]]:
        res = await self.service.list_goals(session_id=session_id, caller=caller)
        return success_response(data=res)

    async def update_goal(
        self, caller: UserInDB, goal_id: str, req: UpdateTherapyGoalRequest
    ) -> ApiResponse[TherapyGoalResponse]:
        res = await self.service.update_goal(goal_id=goal_id, caller=caller, req=req)
        return success_response(data=res, message="Therapy goal updated successfully")

    async def get_therapist_dashboard(
        self, caller: UserInDB
    ) -> ApiResponse[TherapistDashboardSummaryResponse]:
        res = await self.service.get_therapist_dashboard(caller=caller)
        return success_response(data=res)

    async def list_therapist_sessions(
        self,
        caller: UserInDB,
        status: SessionStatus | None,
        date_filter: str | None,
        page: int,
        limit: int,
    ) -> ApiResponse[list[SessionResponse]]:
        skip = (page - 1) * limit
        res = await self.service.list_therapist_sessions(
            caller=caller,
            status=status,
            date_filter=date_filter,
            skip=skip,
            limit=limit,
        )
        return success_response(data=res)

    async def list_client_sessions(
        self, caller: UserInDB, status: SessionStatus | None, page: int, limit: int
    ) -> ApiResponse[list[ClientSessionResponse]]:
        skip = (page - 1) * limit
        res = await self.service.list_client_sessions(
            caller=caller, status=status, skip=skip, limit=limit
        )
        return success_response(data=res)
