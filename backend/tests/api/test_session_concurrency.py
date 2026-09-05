"""Concurrency test for atomic session start operations."""

import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from mongomock_motor import AsyncMongoMockClient

from app.modules.session.session_constants import AttendanceStatus, SessionStatus
from app.modules.session.session_model import SessionInDB
from app.modules.session.session_repository import SessionRepository


@pytest.mark.asyncio
async def test_atomic_session_start_concurrency() -> None:
    """Ensure that concurrent start requests atomically transition session once without duplicate starts."""
    mock_client: Any = AsyncMongoMockClient()
    mock_db = mock_client["oppam_therapy_test"]
    repo = SessionRepository(mock_db)

    now = datetime.now(UTC)
    session = SessionInDB(
        id=f"sess_{uuid.uuid4().hex[:12]}",
        booking_id=f"bk_{uuid.uuid4().hex[:12]}",
        therapist_id="th_concurrent_123",
        client_id="cl_concurrent_123",
        scheduled_start_at=now,
        scheduled_end_at=now + timedelta(hours=1),
        duration_minutes=60,
        session_mode="online",
        status=SessionStatus.SCHEDULED,
        attendance=AttendanceStatus.UNKNOWN,
    )
    await repo.create_session(session)

    # Launch 5 concurrent start attempts
    results = await asyncio.gather(
        *(repo.start_session_atomic(session.id, started_at=now) for _ in range(5))
    )

    # Exactly 1 returns the newly transitioned SessionInDB, 4 return None (transition condition failed)
    successes = [r for r in results if r is not None]
    failures = [r for r in results if r is None]

    assert len(successes) == 1
    assert len(failures) == 4

    # Final DB record is verified IN_PROGRESS
    final_session = await repo.get_session_by_id(session.id)
    assert final_session is not None
    assert final_session.status == SessionStatus.IN_PROGRESS
