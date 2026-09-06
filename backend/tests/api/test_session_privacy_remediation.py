"""Tests verifying strict isolation of session-scoped goals and clinical notes privacy."""

from datetime import UTC, datetime
from typing import Any

import pytest
from httpx import AsyncClient

from app.modules.session.session_constants import AttendanceStatus, SessionStatus
from app.modules.session.session_model import SessionInDB, SessionNoteInDB


@pytest.mark.asyncio
async def test_session_goals_isolation_between_sessions_of_same_client(
    client: AsyncClient, mock_db: Any
) -> None:
    """Goals for Session A must NOT be returned when querying Session B, even for the same client."""
    # 1. Register therapist & client
    reg_th = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Jayasurya",
            "last_name": "M",
            "email": "jayasurya@example.com",
            "password": "Password123!",
        },
    )
    th_token = reg_th.json()["data"]["access_token"]
    reg_th.json()["data"]["user"]["id"]
    th_headers = {"Authorization": f"Bearer {th_token}"}

    th_res = await client.post(
        "/api/v1/therapists",
        headers=th_headers,
        json={
            "first_name": "Jayasurya",
            "last_name": "M",
            "display_name": "Dr. Jayasurya",
            "bio": "Clinical psychologist.",
            "designation": "Psychologist",
            "specialization": "clinical_psychologist",
            "qualifications": ["Ph.D"],
            "experience_years": 8,
            "therapy_hours": 1200,
            "languages": ["ml", "en"],
            "expertises": ["anxiety"],
            "session_modes": ["online"],
            "pricing": {"amount": 1000, "currency": "INR", "duration_minutes": 60},
        },
    )
    therapist_id = th_res.json()["data"]["id"]

    reg_cl = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Asif",
            "last_name": "Ali",
            "email": "asif@example.com",
            "password": "Password123!",
        },
    )
    client_id = reg_cl.json()["data"]["user"]["id"]
    cl_token = reg_cl.json()["data"]["access_token"]
    cl_headers = {"Authorization": f"Bearer {cl_token}"}

    now = datetime.now(UTC)

    # 2. Seed two distinct sessions for the same client
    session_a = SessionInDB(
        id="session-a-1111",
        booking_id="booking-a",
        therapist_id=therapist_id,
        client_id=client_id,
        scheduled_start_at=now,
        scheduled_end_at=now,
        duration_minutes=60,
        session_mode="online",
        status=SessionStatus.COMPLETED,
        attendance=AttendanceStatus.PRESENT,
    )
    session_b = SessionInDB(
        id="session-b-2222",
        booking_id="booking-b",
        therapist_id=therapist_id,
        client_id=client_id,
        scheduled_start_at=now,
        scheduled_end_at=now,
        duration_minutes=60,
        session_mode="online",
        status=SessionStatus.COMPLETED,
        attendance=AttendanceStatus.PRESENT,
    )
    await mock_db["sessions"].insert_many([session_a.model_dump(), session_b.model_dump()])

    # 3. Create Goal for Session A
    goal_a_res = await client.post(
        "/api/v1/sessions/session-a-1111/goals",
        headers=th_headers,
        json={"title": "Goal for Session A", "description": "Reduce anxiety symptoms"},
    )
    assert goal_a_res.status_code == 201

    # 4. Create Goal for Session B
    goal_b_res = await client.post(
        "/api/v1/sessions/session-b-2222/goals",
        headers=th_headers,
        json={"title": "Goal for Session B", "description": "Improve sleep schedule"},
    )
    assert goal_b_res.status_code == 201

    # 5. Query goals for Session A -> must return ONLY Goal A
    get_a = await client.get("/api/v1/sessions/session-a-1111/goals", headers=cl_headers)
    assert get_a.status_code == 200
    goals_a = get_a.json()["data"]
    assert len(goals_a) == 1
    assert goals_a[0]["title"] == "Goal for Session A"

    # 6. Query goals for Session B -> must return ONLY Goal B
    get_b = await client.get("/api/v1/sessions/session-b-2222/goals", headers=cl_headers)
    assert get_b.status_code == 200
    goals_b = get_b.json()["data"]
    assert len(goals_b) == 1
    assert goals_b[0]["title"] == "Goal for Session B"


@pytest.mark.asyncio
async def test_client_cannot_access_therapist_private_notes(
    client: AsyncClient, mock_db: Any
) -> None:
    """Client endpoint only exposes public summary; therapist private notes remain private."""
    now = datetime.now(UTC)
    note = SessionNoteInDB(
        id="note-1234",
        session_id="session-private-1",
        therapist_id="th-1234",
        client_id="client-5678",
        summary="Patient shows steady improvement.",
        private_notes="CONFIDENTIAL: Patient expressed deep unresolved childhood trauma.",
        created_at=now,
        updated_at=now,
    )
    session = SessionInDB(
        id="session-private-1",
        booking_id="booking-p1",
        therapist_id="th-1234",
        client_id="client-5678",
        scheduled_start_at=now,
        scheduled_end_at=now,
        duration_minutes=60,
        session_mode="online",
        status=SessionStatus.COMPLETED,
    )
    await mock_db["sessions"].insert_one(session.model_dump())
    await mock_db["session_notes"].insert_one(note.model_dump())

    # Register the client
    reg_cl = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Tovino",
            "last_name": "Thomas",
            "email": "tovino@example.com",
            "password": "Password123!",
        },
    )
    cl_token = reg_cl.json()["data"]["access_token"]
    client_actual_id = reg_cl.json()["data"]["user"]["id"]
    cl_headers = {"Authorization": f"Bearer {cl_token}"}

    # Update session to belong to Tovino
    await mock_db["sessions"].update_one(
        {"id": "session-private-1"},
        {"$set": {"client_id": client_actual_id}},
    )

    # Client fetches their note view
    cl_res = await client.get(
        "/api/v1/sessions/session-private-1/notes/client",
        headers=cl_headers,
    )
    assert cl_res.status_code == 200
    data = cl_res.json()["data"]
    assert "summary" in data
    assert data["summary"] == "Patient shows steady improvement."
    assert "private_notes" not in data

    # Client tries to fetch therapist full note endpoint -> 403 Forbidden
    th_note_res = await client.get(
        "/api/v1/sessions/session-private-1/notes",
        headers=cl_headers,
    )
    assert th_note_res.status_code == 403
