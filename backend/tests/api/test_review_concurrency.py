"""Concurrency test verifying exactly one review can be created per completed session under contention."""

import asyncio
from datetime import UTC, datetime
from typing import Any

import pytest
from httpx import AsyncClient

from app.modules.review.review_repository import ReviewRepository
from app.modules.session.session_constants import SessionStatus
from tests.api.test_session_lifecycle import _setup_confirmed_booking


@pytest.mark.asyncio
async def test_concurrent_review_submission_mutual_exclusion(
    client: AsyncClient, mock_db: Any
) -> None:
    """Ensure database-level unique index on session_id prevents duplicate reviews under concurrent flood."""
    # Ensure indexes are built in mock db
    await ReviewRepository(mock_db).create_indexes()

    booking_id, therapist_id, client_id, th_token, cl_token = (
        await _setup_confirmed_booking(
            client, mock_db, offset_days=2, start_time="14:00", end_time="15:00"
        )
    )
    cl_headers = {"Authorization": f"Bearer {cl_token}"}

    # Retrieve auto-created session and complete it
    session_doc = await mock_db["sessions"].find_one({"booking_id": booking_id})
    assert session_doc is not None
    session_id = session_doc["id"]

    await mock_db["sessions"].update_one(
        {"id": session_id},
        {"$set": {"status": SessionStatus.COMPLETED.value, "ended_at": datetime.now(UTC)}},
    )

    # Launch 5 concurrent review submission requests
    async def submit() -> int:
        res = await client.post(
            "/api/v1/reviews",
            headers=cl_headers,
            json={
                "session_id": session_id,
                "rating": 5,
                "comment": "Concurrent test submission",
            },
        )
        return res.status_code

    results = await asyncio.gather(*[submit() for _ in range(5)])

    success_count = sum(1 for status in results if status == 201)
    conflict_count = sum(1 for status in results if status == 409)

    # Mutual exclusion invariant: exactly 1 success, 4 conflicts
    assert success_count == 1, f"Expected exactly 1 success, got {success_count}. Results: {results}"
    assert conflict_count == 4, f"Expected 4 conflicts, got {conflict_count}. Results: {results}"

    # Verify exactly 1 document in database
    db_count = await mock_db["reviews"].count_documents({"session_id": session_id})
    assert db_count == 1
