"""Security and Authorization tests for Session and Clinical Notes privacy."""

from typing import Any

import pytest
from httpx import AsyncClient

from tests.api.test_session_lifecycle import _setup_confirmed_booking


@pytest.mark.asyncio
async def test_session_idor_isolation(client: AsyncClient, mock_db: Any) -> None:
    # 1. Setup Session A
    booking_id_a, _, client_id_a, th_token_a, cl_token_a = await _setup_confirmed_booking(
        client, mock_db, offset_days=1, start_time="09:00", end_time="10:00"
    )
    session_a = await mock_db["sessions"].find_one({"booking_id": booking_id_a})
    session_id_a = session_a["id"]

    # 2. Setup Session B with distinct Therapist B and Client B
    _, _, _, th_token_b, cl_token_b = await _setup_confirmed_booking(
        client, mock_db, offset_days=1, start_time="15:00", end_time="16:00"
    )

    headers_th_b = {"Authorization": f"Bearer {th_token_b}"}
    headers_cl_b = {"Authorization": f"Bearer {cl_token_b}"}

    # Therapist B attempts to view Session A -> 403 Forbidden
    th_b_view = await client.get(f"/api/v1/sessions/{session_id_a}", headers=headers_th_b)
    assert th_b_view.status_code == 403
    assert th_b_view.json()["error"]["code"] == "SESSION_FORBIDDEN"

    # Client B attempts to view Session A -> 403 Forbidden
    cl_b_view = await client.get(f"/api/v1/sessions/{session_id_a}", headers=headers_cl_b)
    assert cl_b_view.status_code == 403
    assert cl_b_view.json()["error"]["code"] == "SESSION_FORBIDDEN"

    # Therapist B attempts to start Session A -> 403 Forbidden
    th_b_start = await client.post(f"/api/v1/sessions/{session_id_a}/start", headers=headers_th_b)
    assert th_b_start.status_code == 403


@pytest.mark.asyncio
async def test_clinical_notes_privacy_boundary(client: AsyncClient, mock_db: Any) -> None:
    booking_id, _, _, th_token, cl_token = await _setup_confirmed_booking(
        client, mock_db, offset_days=1, start_time="11:00", end_time="12:00"
    )
    session = await mock_db["sessions"].find_one({"booking_id": booking_id})
    session_id = session["id"]

    th_headers = {"Authorization": f"Bearer {th_token}"}
    cl_headers = {"Authorization": f"Bearer {cl_token}"}

    # 1. Therapist creates clinical notes with confidential private section
    save_note = await client.post(
        f"/api/v1/sessions/{session_id}/notes",
        headers=th_headers,
        json={
            "summary": "Client discussed work-life stress and boundary management.",
            "private_notes": "CONFIDENTIAL: Possible mild depressive symptoms; evaluate sleep cycle next week.",
        },
    )
    assert save_note.status_code == 200
    assert save_note.json()["data"]["private_notes"] != ""

    # 2. Client attempts to access therapist's private notes endpoint -> 403 Forbidden
    cl_private_attempt = await client.get(f"/api/v1/sessions/{session_id}/notes", headers=cl_headers)
    assert cl_private_attempt.status_code == 403

    # 3. Client accesses public client-facing summary note endpoint
    cl_summary_res = await client.get(f"/api/v1/sessions/{session_id}/notes/client", headers=cl_headers)
    assert cl_summary_res.status_code == 200
    cl_data = cl_summary_res.json()["data"]
    assert cl_data["summary"] == "Client discussed work-life stress and boundary management."
    # STRICT INVARIANT: private_notes is NOT in client data envelope
    assert "private_notes" not in cl_data


@pytest.mark.asyncio
async def test_therapy_goals_crud_and_permissions(client: AsyncClient, mock_db: Any) -> None:
    booking_id, _, _, th_token, cl_token = await _setup_confirmed_booking(
        client, mock_db, offset_days=1, start_time="12:00", end_time="13:00"
    )
    session = await mock_db["sessions"].find_one({"booking_id": booking_id})
    session_id = session["id"]

    th_headers = {"Authorization": f"Bearer {th_token}"}
    cl_headers = {"Authorization": f"Bearer {cl_token}"}

    # 1. Therapist creates therapy goal
    create_goal = await client.post(
        f"/api/v1/sessions/{session_id}/goals",
        headers=th_headers,
        json={
            "title": "Establish sleep hygiene routine",
            "description": "Maintain regular 11 PM sleep schedule with no screens 30 mins prior.",
        },
    )
    assert create_goal.status_code == 201
    goal_id = create_goal.json()["data"]["id"]
    assert create_goal.json()["data"]["status"] == "active"

    # 2. Both therapist and client can list goals
    th_goals = await client.get(f"/api/v1/sessions/{session_id}/goals", headers=th_headers)
    assert th_goals.status_code == 200
    assert len(th_goals.json()["data"]) >= 1

    cl_goals = await client.get(f"/api/v1/sessions/{session_id}/goals", headers=cl_headers)
    assert cl_goals.status_code == 200
    assert len(cl_goals.json()["data"]) >= 1

    # 3. Client attempts to mutate goal -> 403 Forbidden (Therapist only)
    cl_patch = await client.patch(
        f"/api/v1/sessions/goals/{goal_id}",
        headers=cl_headers,
        json={"status": "completed"},
    )
    assert cl_patch.status_code == 403

    # 4. Therapist updates goal to completed
    th_patch = await client.patch(
        f"/api/v1/sessions/goals/{goal_id}",
        headers=th_headers,
        json={"status": "completed"},
    )
    assert th_patch.status_code == 200
    assert th_patch.json()["data"]["status"] == "completed"
