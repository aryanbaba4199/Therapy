"""Integration tests for Review & Rating lifecycle: submission, eligibility, uniqueness, and aggregation."""

import uuid
from datetime import UTC, datetime
from typing import Any

import pytest
from httpx import AsyncClient

from app.modules.session.session_constants import SessionStatus
from tests.api.test_session_lifecycle import _setup_confirmed_booking


@pytest.mark.asyncio
async def test_review_submission_and_eligibility(
    client: AsyncClient, mock_db: Any
) -> None:
    """Test full review eligibility matrix: only completed sessions owned by caller can be reviewed."""
    booking_id, therapist_id, client_id, _th_token, cl_token = (
        await _setup_confirmed_booking(client, mock_db, offset_days=1, start_time="10:00", end_time="11:00")
    )
    cl_headers = {"Authorization": f"Bearer {cl_token}"}

    # Session was auto-created upon booking confirmation
    session_doc = await mock_db["sessions"].find_one({"booking_id": booking_id})
    assert session_doc is not None
    session_id = session_doc["id"]

    # 1. Non-existent session
    fake_id = str(uuid.uuid4())
    res_not_found = await client.post(
        "/api/v1/reviews",
        headers=cl_headers,
        json={"session_id": fake_id, "rating": 5, "comment": "Great!"},
    )
    assert res_not_found.status_code == 404
    assert res_not_found.json()["error"]["code"] == "SESSION_NOT_FOUND"

    # 2. Session is SCHEDULED (not COMPLETED)
    res_not_eligible = await client.post(
        "/api/v1/reviews",
        headers=cl_headers,
        json={"session_id": session_id, "rating": 5, "comment": "Great!"},
    )
    assert res_not_eligible.status_code == 400
    assert res_not_eligible.json()["error"]["code"] == "REVIEW_NOT_ELIGIBLE"

    # 3. Create another user (Client B)
    reg_b = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Bob",
            "last_name": "Dylan",
            "email": f"bob.{uuid.uuid4().hex[:6]}@example.com",
            "password": "Password123!",
        },
    )
    cl_b_token = reg_b.json()["data"]["access_token"]
    cl_b_headers = {"Authorization": f"Bearer {cl_b_token}"}

    # Mark session COMPLETED directly in DB
    await mock_db["sessions"].update_one(
        {"id": session_id},
        {"$set": {"status": SessionStatus.COMPLETED.value, "ended_at": datetime.now(UTC)}},
    )

    # 4. Client B attempts to review Client A's session -> IDOR rejection (403)
    res_forbidden = await client.post(
        "/api/v1/reviews",
        headers=cl_b_headers,
        json={"session_id": session_id, "rating": 5, "comment": "Trying to review"},
    )
    assert res_forbidden.status_code == 403
    assert res_forbidden.json()["error"]["code"] == "REVIEW_FORBIDDEN"

    # 5. Invalid rating bounds
    res_invalid_rating = await client.post(
        "/api/v1/reviews",
        headers=cl_headers,
        json={"session_id": session_id, "rating": 0, "comment": "Zero stars"},
    )
    assert res_invalid_rating.status_code in [400, 422]

    res_too_high = await client.post(
        "/api/v1/reviews",
        headers=cl_headers,
        json={"session_id": session_id, "rating": 6, "comment": "Six stars"},
    )
    assert res_too_high.status_code in [400, 422]

    # 6. Valid review submission by legitimate client
    res_valid = await client.post(
        "/api/v1/reviews",
        headers=cl_headers,
        json={
            "session_id": session_id,
            "rating": 5,
            "comment": "Exceptional consultation, very empathetic!",
            "is_anonymous": False,
        },
    )
    assert res_valid.status_code == 201
    review_data = res_valid.json()["data"]
    review_id = review_data["id"]
    assert review_id
    assert review_data["rating"] == 5
    assert review_data["therapist_id"] == therapist_id
    assert review_data["client_id"] == client_id
    assert "Exceptional" in review_data["comment"]

    # Test fetching review directly by ID
    res_get_by_id = await client.get(f"/api/v1/reviews/{review_id}", headers=cl_headers)
    assert res_get_by_id.status_code == 200
    assert res_get_by_id.json()["data"]["id"] == review_id

    # 7. Duplicate review attempt on same completed session -> 409 Conflict
    res_duplicate = await client.post(
        "/api/v1/reviews",
        headers=cl_headers,
        json={"session_id": session_id, "rating": 4, "comment": "Second review"},
    )
    assert res_duplicate.status_code == 409
    assert res_duplicate.json()["error"]["code"] == "REVIEW_ALREADY_EXISTS"

    # 8. Query client review history
    res_history = await client.get("/api/v1/reviews/my/history", headers=cl_headers)
    assert res_history.status_code == 200
    assert len(res_history.json()["data"]) >= 1

    # 9. Query public reviews on therapist profile
    res_pub = await client.get(f"/api/v1/reviews/therapist/{therapist_id}")
    assert res_pub.status_code == 200
    pub_items = res_pub.json()["data"]
    assert len(pub_items) >= 1
    assert pub_items[0]["rating"] == 5

    # 10. Query therapist aggregate rating summary
    res_summary = await client.get(f"/api/v1/reviews/therapist/{therapist_id}/summary")
    assert res_summary.status_code == 200
    summary_data = res_summary.json()["data"]
    assert summary_data["therapist_id"] == therapist_id
    assert summary_data["average_rating"] == 5.0
    assert summary_data["review_count"] == 1
    assert summary_data["distribution"]["5"] == 1
