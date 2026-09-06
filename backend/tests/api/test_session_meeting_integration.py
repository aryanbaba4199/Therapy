"""Integration tests for Session Google Meet provisioning, resilience, and retry."""

import asyncio
from datetime import date, timedelta
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.modules.session.providers.meeting_provider import MeetingCreationResult
from app.modules.session.session_constants import MeetingProviderType, MeetingStatus


async def _setup_booking(
    client: AsyncClient,
    mock_db: Any,
    session_mode: str = "online",
    offset_days: int = 1,
    start_time: str = "10:00",
    end_time: str = "11:00",
) -> tuple[str, str, str, str, str]:
    """Helper to set up therapist, client, and confirmed booking."""
    unique_suffix = f"{session_mode[:3]}.{date.today().isoformat()}.{start_time.replace(':', '')}"
    th_email = f"doc.{unique_suffix}@example.com"
    th_reg = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Deepak",
            "last_name": "Nambiar",
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
            "first_name": "Deepak",
            "last_name": "Nambiar",
            "display_name": "Dr. Deepak Nambiar",
            "bio": "Experienced therapist in Kozhikode",
            "designation": "Clinical Psychologist",
            "specialization": "clinical_psychologist",
            "qualifications": ["PhD Clinical Psychology"],
            "experience_years": 10,
            "therapy_hours": 3000,
            "languages": ["ml", "en"],
            "expertises": ["anxiety", "depression"],
            "session_modes": [session_mode],
            "pricing": {"amount": 1200, "currency": "INR", "duration_minutes": 60},
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
            "session_mode": session_mode,
        },
    )
    slots_res = await client.get(
        f"/api/v1/therapists/{therapist_id}/slots?date={slot_date}&session_mode={session_mode}",
        headers=th_headers,
    )
    slot_id = slots_res.json()["data"][0]["id"]

    cl_email = f"client.{unique_suffix}@example.com"
    cl_reg = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Suresh",
            "last_name": "Menon",
            "email": cl_email,
            "password": "Password123!",
        },
    )
    cl_user_id = cl_reg.json()["data"]["user"]["id"]
    cl_token = cl_reg.json()["data"]["access_token"]
    cl_headers = {"Authorization": f"Bearer {cl_token}"}

    res_hold = await client.post(
        "/api/v1/bookings/reservations",
        headers=cl_headers,
        json={
            "therapist_id": therapist_id,
            "slot_id": slot_id,
            "slot_date": slot_date,
            "session_mode": session_mode,
        },
    )
    reservation_id = res_hold.json()["data"]["id"]

    book_res = await client.post(
        "/api/v1/bookings/confirm",
        headers=cl_headers,
        json={"reservation_id": reservation_id, "client_notes": "Online Meet Test"},
    )
    assert book_res.status_code == 201
    booking_id = book_res.json()["data"]["id"]

    return booking_id, therapist_id, cl_user_id, th_token, cl_token


@pytest.mark.asyncio
async def test_online_session_creates_google_meet(client: AsyncClient, mock_db: Any) -> None:
    booking_id, therapist_id, client_id, th_token, cl_token = await _setup_booking(
        client, mock_db, session_mode="online", offset_days=1, start_time="14:00", end_time="15:00"
    )
    th_headers = {"Authorization": f"Bearer {th_token}"}
    cl_headers = {"Authorization": f"Bearer {cl_token}"}

    # 1. Inspect DB record
    session_doc = await mock_db["sessions"].find_one({"booking_id": booking_id})
    assert session_doc is not None
    session_id = session_doc["id"]
    assert session_doc["session_mode"] == "online"

    meeting_data = session_doc.get("meeting")
    assert meeting_data is not None
    assert meeting_data["status"] == MeetingStatus.READY.value
    assert meeting_data["join_url"] is not None
    assert "https://meet.google.com/" in meeting_data["join_url"]

    # 2. Client view
    cl_res = await client.get(f"/api/v1/sessions/{session_id}/client-view", headers=cl_headers)
    assert cl_res.status_code == 200
    cl_meeting = cl_res.json()["data"]["meeting"]
    assert cl_meeting["status"] == "ready"
    assert cl_meeting["join_url"] == meeting_data["join_url"]

    # 3. Therapist view
    th_res = await client.get(f"/api/v1/sessions/{session_id}", headers=th_headers)
    assert th_res.status_code == 200
    th_meeting = th_res.json()["data"]["meeting"]
    assert th_meeting["status"] == "ready"
    assert th_meeting["join_url"] == meeting_data["join_url"]


@pytest.mark.asyncio
async def test_offline_session_does_not_provision_meeting(client: AsyncClient, mock_db: Any) -> None:
    booking_id, therapist_id, client_id, th_token, cl_token = await _setup_booking(
        client, mock_db, session_mode="offline_kozhikode", offset_days=1, start_time="16:00", end_time="17:00"
    )
    cl_headers = {"Authorization": f"Bearer {cl_token}"}

    session_doc = await mock_db["sessions"].find_one({"booking_id": booking_id})
    assert session_doc is not None
    session_id = session_doc["id"]

    meeting_data = session_doc.get("meeting")
    assert meeting_data is not None
    assert meeting_data["status"] == MeetingStatus.NOT_REQUIRED.value
    assert meeting_data.get("join_url") is None

    # Client view verifies NOT_REQUIRED
    cl_res = await client.get(f"/api/v1/sessions/{session_id}/client-view", headers=cl_headers)
    assert cl_res.status_code == 200
    cl_meeting = cl_res.json()["data"]["meeting"]
    assert cl_meeting["status"] == "not_required"
    assert cl_meeting["join_url"] is None


@pytest.mark.asyncio
async def test_meeting_failure_resilience_and_retry(client: AsyncClient, mock_db: Any) -> None:
    # Simulate meeting provider failure during booking confirmation
    failing_result = MeetingCreationResult(
        provider=MeetingProviderType.MOCK,
        status=MeetingStatus.FAILED,
        error_message="Google Calendar API 503 Service Unavailable",
    )

    with patch("app.modules.session.providers.mock_meeting_provider.MockMeetingProvider.create_meeting", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = failing_result

        booking_id, therapist_id, client_id, th_token, cl_token = await _setup_booking(
            client, mock_db, session_mode="online", offset_days=2, start_time="09:00", end_time="10:00"
        )

    th_headers = {"Authorization": f"Bearer {th_token}"}
    cl_headers = {"Authorization": f"Bearer {cl_token}"}

    # 1. Session and Booking MUST be intact even if Google Meet failed
    session_doc = await mock_db["sessions"].find_one({"booking_id": booking_id})
    assert session_doc is not None
    assert session_doc["status"] == "scheduled"
    session_id = session_doc["id"]

    meeting_data = session_doc.get("meeting")
    assert meeting_data is not None
    assert meeting_data["status"] == MeetingStatus.FAILED.value
    assert "503" in (meeting_data.get("error_message") or "")

    # 2. Client retry meeting endpoint repairs the meeting
    retry_res = await client.post(f"/api/v1/sessions/{session_id}/meeting/retry", headers=cl_headers)
    assert retry_res.status_code == 200
    retried_meeting = retry_res.json()["data"]["meeting"]
    assert retried_meeting["status"] == "ready"
    assert retried_meeting["join_url"] is not None
    assert "https://meet.google.com/" in retried_meeting["join_url"]

    # 3. Verify DB is updated and therapist can view the updated meeting
    updated_doc = await mock_db["sessions"].find_one({"id": session_id})
    assert updated_doc["meeting"]["status"] == MeetingStatus.READY.value
    assert updated_doc["meeting"]["join_url"] == retried_meeting["join_url"]

    th_res = await client.get(f"/api/v1/sessions/{session_id}", headers=th_headers)
    assert th_res.status_code == 200
    assert th_res.json()["data"]["meeting"]["status"] == "ready"


@pytest.mark.asyncio
async def test_retry_meeting_authorization_and_validation(client: AsyncClient, mock_db: Any) -> None:
    # 1. Setup online session
    booking_id, therapist_id, client_id, th_token, cl_token = await _setup_booking(
        client, mock_db, session_mode="online", offset_days=3, start_time="12:00", end_time="13:00"
    )
    session_doc = await mock_db["sessions"].find_one({"booking_id": booking_id})
    session_id = session_doc["id"]

    # 2. Setup unrelated third-party user
    unauth_reg = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Mallory",
            "last_name": "Intruder",
            "email": "mallory.meet.test@example.com",
            "password": "Password123!",
        },
    )
    unauth_token = unauth_reg.json()["data"]["access_token"]
    unauth_headers = {"Authorization": f"Bearer {unauth_token}"}

    # Third party attempts retry -> 403 Forbidden
    unauth_res = await client.post(f"/api/v1/sessions/{session_id}/meeting/retry", headers=unauth_headers)
    assert unauth_res.status_code == 403

    # 3. Setup offline session and try retry -> 400 Bad Request
    off_booking_id, _, _, off_th_token, _ = await _setup_booking(
        client, mock_db, session_mode="offline_kozhikode", offset_days=3, start_time="14:00", end_time="15:00"
    )
    off_doc = await mock_db["sessions"].find_one({"booking_id": off_booking_id})
    off_session_id = off_doc["id"]
    off_th_headers = {"Authorization": f"Bearer {off_th_token}"}

    off_retry = await client.post(f"/api/v1/sessions/{off_session_id}/meeting/retry", headers=off_th_headers)
    assert off_retry.status_code == 400
    assert off_retry.json()["error"]["code"] == "SESSION_INVALID_STATE"


@pytest.mark.asyncio
async def test_concurrent_meeting_provisioning_idempotency(client: AsyncClient, mock_db: Any) -> None:
    booking_id, _, _, _, _ = await _setup_booking(
        client, mock_db, session_mode="online", offset_days=4, start_time="15:00", end_time="16:00"
    )
    session_doc = await mock_db["sessions"].find_one({"booking_id": booking_id})
    session_id = session_doc["id"]

    # Reset meeting status to NOT_STARTED to test concurrent provisioning
    await mock_db["sessions"].update_one(
        {"id": session_id},
        {"$set": {"meeting": {"provider": "mock", "status": "not_started"}}},
    )

    from app.core.config import get_settings
    from app.modules.booking.booking_repository import BookingRepository
    from app.modules.session.providers.mock_meeting_provider import MockMeetingProvider
    from app.modules.session.session_repository import SessionRepository
    from app.modules.session.session_service import SessionService
    from app.modules.therapist.therapist_repository import TherapistRepository

    service = SessionService(
        session_repo=SessionRepository(mock_db),
        booking_repo=BookingRepository(mock_db),
        therapist_repo=TherapistRepository(mock_db),
        settings=get_settings(),
        meeting_provider=MockMeetingProvider(),
    )

    # Launch 20 concurrent provisioning requests for the same session
    tasks = [service.provision_meeting(session_id) for _ in range(20)]
    results = await asyncio.gather(*tasks)

    # All results must have valid meeting
    assert len(results) == 20
    first_url = results[0].meeting.join_url if results[0].meeting else None
    assert first_url is not None

    for res in results:
        assert res.meeting is not None
        assert res.meeting.status == MeetingStatus.READY
        assert res.meeting.join_url == first_url
