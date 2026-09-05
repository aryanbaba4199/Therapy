"""Integration tests for Session lifecycle: creation, timing windows, start, complete, attendance, and dashboard."""

from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest
from httpx import AsyncClient


async def _setup_confirmed_booking(
    client: AsyncClient, mock_db: Any, offset_days: int = 1, start_time: str = "10:00", end_time: str = "11:00"
) -> tuple[str, str, str, str, str]:
    """Helper to set up therapist, client, and confirmed booking.
    Returns (booking_id, therapist_id, client_id, therapist_token, client_token).
    """
    # 1. Therapist setup
    th_email = f"doc.{date.today().isoformat()}.{start_time.replace(':', '')}@example.com"
    th_reg = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Arun",
            "last_name": "Kumar",
            "email": th_email,
            "password": "Password123!",
        },
    )
    th_user_id = th_reg.json()["data"]["user"]["id"]
    th_token = th_reg.json()["data"]["access_token"]
    th_headers = {"Authorization": f"Bearer {th_token}"}
    await mock_db["users"].update_one({"id": th_user_id}, {"$set": {"roles": ["therapist"]}})

    th_res = await client.post(
        "/api/v1/therapists",
        headers=th_headers,
        json={
            "first_name": "Arun",
            "last_name": "Kumar",
            "display_name": "Dr. Arun Kumar",
            "bio": "Experienced therapist in Calicut",
            "designation": "Consultant Psychologist",
            "specialization": "clinical_psychologist",
            "qualifications": ["M.Phil Psychology"],
            "experience_years": 7,
            "therapy_hours": 1200,
            "languages": ["ml", "en"],
            "expertises": ["stress"],
            "session_modes": ["online"],
            "pricing": {"amount": 1000, "currency": "INR", "duration_minutes": 60},
        },
    )
    therapist_id = th_res.json()["data"]["id"]
    await mock_db["therapists"].update_one(
        {"id": therapist_id},
        {"$set": {"status": "active", "verification.status": "verified"}},
    )

    slot_date = (date.today() + timedelta(days=offset_days)).isoformat()
    await client.post(
        f"/api/v1/therapists/{therapist_id}/extra-slots",
        headers=th_headers,
        json={
            "date": slot_date,
            "start_time": start_time,
            "end_time": end_time,
            "session_mode": "online",
        },
    )
    slots_res = await client.get(
        f"/api/v1/therapists/{therapist_id}/slots?date={slot_date}",
        headers=th_headers,
    )
    slot_id = slots_res.json()["data"][0]["id"]

    # 2. Client setup
    cl_email = f"client.{date.today().isoformat()}.{start_time.replace(':', '')}@example.com"
    cl_reg = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Deepa",
            "last_name": "Menon",
            "email": cl_email,
            "password": "Password123!",
        },
    )
    cl_user_id = cl_reg.json()["data"]["user"]["id"]
    cl_token = cl_reg.json()["data"]["access_token"]
    cl_headers = {"Authorization": f"Bearer {cl_token}"}

    # 3. Reserve slot
    res_hold = await client.post(
        "/api/v1/bookings/reservations",
        headers=cl_headers,
        json={
            "therapist_id": therapist_id,
            "slot_id": slot_id,
            "slot_date": slot_date,
            "session_mode": "online",
        },
    )
    reservation_id = res_hold.json()["data"]["id"]

    # 4. Confirm booking
    book_res = await client.post(
        "/api/v1/bookings/confirm",
        headers=cl_headers,
        json={"reservation_id": reservation_id, "client_notes": "Initial consultation"},
    )
    assert book_res.status_code == 201
    booking_id = book_res.json()["data"]["id"]

    return booking_id, therapist_id, cl_user_id, th_token, cl_token


@pytest.mark.asyncio
async def test_session_auto_creation_and_timing_window(client: AsyncClient, mock_db: Any) -> None:
    booking_id, therapist_id, client_id, th_token, cl_token = await _setup_confirmed_booking(
        client, mock_db, offset_days=2, start_time="11:00", end_time="12:00"
    )
    th_headers = {"Authorization": f"Bearer {th_token}"}
    cl_headers = {"Authorization": f"Bearer {cl_token}"}

    # 1. Verify session was automatically created for confirmed booking
    session_doc = await mock_db["sessions"].find_one({"booking_id": booking_id})
    assert session_doc is not None
    session_id = session_doc["id"]
    assert session_doc["status"] == "scheduled"
    assert session_doc["therapist_id"] == therapist_id
    assert session_doc["client_id"] == client_id

    # 2. Therapist fetches session details
    get_res = await client.get(f"/api/v1/sessions/{session_id}", headers=th_headers)
    assert get_res.status_code == 200
    assert get_res.json()["data"]["id"] == session_id

    # 3. Client fetches sanitized client view
    cl_view = await client.get(f"/api/v1/sessions/{session_id}/client-view", headers=cl_headers)
    assert cl_view.status_code == 200
    assert cl_view.json()["data"]["booking_id"] == booking_id

    # 4. Attempt to start session prematurely (offset is 2 days ahead, window is 15 mins)
    start_fail = await client.post(f"/api/v1/sessions/{session_id}/start", headers=th_headers)
    assert start_fail.status_code == 400
    assert start_fail.json()["error"]["code"] == "SESSION_START_TOO_EARLY"


@pytest.mark.asyncio
async def test_session_start_complete_and_attendance(client: AsyncClient, mock_db: Any) -> None:
    booking_id, _, _, th_token, _ = await _setup_confirmed_booking(
        client, mock_db, offset_days=1, start_time="14:00", end_time="15:00"
    )
    th_headers = {"Authorization": f"Bearer {th_token}"}

    session_doc = await mock_db["sessions"].find_one({"booking_id": booking_id})
    assert session_doc is not None
    session_id = session_doc["id"]

    # Adjust scheduled_start_at to right now so start window is valid
    now = datetime.now(UTC)
    await mock_db["sessions"].update_one(
        {"id": session_id},
        {
            "$set": {
                "scheduled_start_at": now + timedelta(minutes=5),
                "scheduled_end_at": now + timedelta(minutes=65),
            }
        },
    )

    # 1. Start session
    start_res = await client.post(f"/api/v1/sessions/{session_id}/start", headers=th_headers)
    assert start_res.status_code == 200
    assert start_res.json()["data"]["status"] == "in_progress"
    assert start_res.json()["data"]["started_at"] is not None

    # 2. Idempotent start: starting again returns current in_progress state
    start_again = await client.post(f"/api/v1/sessions/{session_id}/start", headers=th_headers)
    assert start_again.status_code == 200
    assert start_again.json()["data"]["status"] == "in_progress"

    # 3. Record attendance
    att_res = await client.post(
        f"/api/v1/sessions/{session_id}/attendance",
        headers=th_headers,
        json={"attendance": "present"},
    )
    assert att_res.status_code == 200
    assert att_res.json()["data"]["attendance"] == "present"

    # 4. Complete session
    comp_res = await client.post(f"/api/v1/sessions/{session_id}/complete", headers=th_headers)
    assert comp_res.status_code == 200
    assert comp_res.json()["data"]["status"] == "completed"
    assert comp_res.json()["data"]["ended_at"] is not None

    # 5. Completing again is idempotent
    comp_again = await client.post(f"/api/v1/sessions/{session_id}/complete", headers=th_headers)
    assert comp_again.status_code == 200
    assert comp_again.json()["data"]["status"] == "completed"


@pytest.mark.asyncio
async def test_therapist_dashboard_and_history(client: AsyncClient, mock_db: Any) -> None:
    booking_id, _therapist_id, _, th_token, cl_token = await _setup_confirmed_booking(
        client, mock_db, offset_days=1, start_time="10:00", end_time="11:00"
    )

    th_headers = {"Authorization": f"Bearer {th_token}"}
    cl_headers = {"Authorization": f"Bearer {cl_token}"}

    # Set scheduled_start_at of session to today (within current UTC day)
    now = datetime.now(UTC)
    start_of_today = datetime(now.year, now.month, now.day, 10, 0, 0, tzinfo=UTC)
    await mock_db["sessions"].update_one(
        {"booking_id": booking_id},
        {
            "$set": {
                "scheduled_start_at": start_of_today,
                "scheduled_end_at": start_of_today + timedelta(hours=1),
            }
        },
    )

    # 1. Get therapist dashboard
    dash_res = await client.get("/api/v1/therapist/portal/dashboard", headers=th_headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()["data"]
    assert "today_sessions_count" in dash_data
    assert len(dash_data["today_sessions"]) >= 1


    # 2. List therapist sessions via portal
    list_res = await client.get("/api/v1/therapist/portal/sessions", headers=th_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()["data"]) >= 1

    # 3. List client sessions
    my_sessions = await client.get("/api/v1/sessions/my/sessions", headers=cl_headers)
    assert my_sessions.status_code == 200
    assert len(my_sessions.json()["data"]) >= 1
    assert my_sessions.json()["data"][0]["booking_id"] == booking_id
