"""Session entity factory for deterministic test data."""

import uuid
from datetime import timedelta
from typing import Any

from app.common.utils.datetime_utils import utc_now
from app.modules.session.session_constants import (
    MeetingProviderType,
    MeetingStatus,
    SessionStatus,
)
from app.modules.session.session_model import SessionInDB, SessionMeetingInDB


class SessionFactory:
    @staticmethod
    def build(
        *,
        id: str | None = None,
        booking_id: str | None = None,
        therapist_id: str | None = None,
        client_id: str | None = None,
        status: SessionStatus = SessionStatus.SCHEDULED,
        session_mode: str = "online",
        scheduled_start_at: Any | None = None,
        duration_minutes: int = 60,
        meeting_url: str | None = None,
    ) -> SessionInDB:
        s_id = id or str(uuid.uuid4())
        b_id = booking_id or str(uuid.uuid4())
        t_id = therapist_id or str(uuid.uuid4())
        c_id = client_id or str(uuid.uuid4())
        now = utc_now()
        start = scheduled_start_at or (now + timedelta(days=1))
        end = start + timedelta(minutes=duration_minutes)

        meeting = None
        if session_mode == "online":
            url = meeting_url or f"https://meet.google.com/test-{s_id[:8]}"
            meeting = SessionMeetingInDB(
                provider=MeetingProviderType.GOOGLE_MEET,
                join_url=url,
                status=MeetingStatus.READY,
                conference_id=f"conf_{s_id[:8]}",
            )

        return SessionInDB(
            id=s_id,
            booking_id=b_id,
            therapist_id=t_id,
            client_id=c_id,
            status=status,
            session_mode=session_mode,
            scheduled_start_at=start,
            scheduled_end_at=end,
            duration_minutes=duration_minutes,
            meeting=meeting,
            created_at=now,
            updated_at=now,
        )

    @staticmethod
    async def create(mock_db: Any, **kwargs: Any) -> SessionInDB:
        session = SessionFactory.build(**kwargs)
        await mock_db["sessions"].insert_one(session.model_dump(mode="json"))
        return session
