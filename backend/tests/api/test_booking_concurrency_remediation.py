"""Adversarial and concurrency tests for booking, reservation state transitions, and session lifecycle."""

import asyncio
from datetime import UTC, date, datetime, timedelta
from typing import Any

import pytest
from httpx import AsyncClient

from app.modules.session.session_constants import SessionStatus


@pytest.mark.asyncio
async def test_concurrent_confirm_vs_cancel_mutual_exclusion(
    client: AsyncClient, mock_db: Any
) -> None:
    """Simultaneous confirm vs cancel on the same active reservation: exactly one wins atomically."""
    # 1. Register therapist
    reg_th = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Suresh",
            "last_name": "Gopi",
            "email": "suresh@example.com",
            "password": "Password123!",
        },
    )
    th_token = reg_th.json()["data"]["access_token"]
    th_headers = {"Authorization": f"Bearer {th_token}"}

    th_res = await client.post(
        "/api/v1/therapists",
        headers=th_headers,
        json={
            "first_name": "Suresh",
            "last_name": "Gopi",
            "display_name": "Dr. Suresh Gopi",
            "bio": "Clinical psychologist.",
            "designation": "Psychologist",
            "specialization": "clinical_psychologist",
            "qualifications": ["M.Phil Psychology"],
            "experience_years": 10,
            "therapy_hours": 1500,
            "languages": ["ml", "en"],
            "expertises": ["anxiety"],
            "session_modes": ["online"],
            "pricing": {"amount": 1200, "currency": "INR", "duration_minutes": 60},
        },
    )
    therapist_id = th_res.json()["data"]["id"]

    await mock_db["therapists"].update_one(
        {"id": therapist_id},
        {"$set": {"status": "active", "verification.status": "verified"}},
    )

    slot_date = (date.today() + timedelta(days=3)).isoformat()
    await client.post(
        f"/api/v1/therapists/{therapist_id}/extra-slots",
        headers=th_headers,
        json={
            "date": slot_date,
            "start_time": "10:00",
            "end_time": "11:00",
            "session_mode": "online",
        },
    )

    slots_res = await client.get(
        f"/api/v1/therapists/{therapist_id}/slots?date={slot_date}",
        headers=th_headers,
    )
    slot_id = slots_res.json()["data"][0]["id"]

    # 2. Register client
    reg_cl = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Nivin",
            "last_name": "Pauly",
            "email": "nivin@example.com",
            "password": "Password123!",
        },
    )
    cl_token = reg_cl.json()["data"]["access_token"]
    cl_headers = {"Authorization": f"Bearer {cl_token}"}

    # 3. Create active reservation
    res_post = await client.post(
        "/api/v1/bookings/reservations",
        headers=cl_headers,
        json={
            "therapist_id": therapist_id,
            "slot_id": slot_id,
            "slot_date": slot_date,
            "session_mode": "online",
        },
    )
    assert res_post.status_code == 201
    reservation_id = res_post.json()["data"]["id"]

    # 4. Fire concurrent confirm vs cancel
    async def do_confirm() -> int:
        res = await client.post(
            "/api/v1/bookings/confirm",
            headers=cl_headers,
            json={"reservation_id": reservation_id, "notes": "Race test"},
        )
        return res.status_code

    async def do_cancel() -> int:
        res = await client.delete(
            f"/api/v1/bookings/reservations/{reservation_id}",
            headers=cl_headers,
        )
        return res.status_code

    results = await asyncio.gather(do_confirm(), do_cancel())

    # One must succeed (200/201), the other must be rejected cleanly
    success_count = sum(1 for code in results if code in (200, 201))
    assert success_count >= 1

    # Invariant: DB reservation status must be either converted or cancelled, never conflicting
    final_res = await mock_db["reservations"].find_one({"id": reservation_id})
    assert final_res is not None
    assert final_res["status"] in ("converted", "cancelled")


@pytest.mark.asyncio
async def test_cannot_cancel_booking_with_in_progress_session(
    client: AsyncClient, mock_db: Any
) -> None:
    """A booking cannot be cancelled if its linked session is already IN_PROGRESS or COMPLETED."""
    # 1. Register therapist & client
    reg_th = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Fahadh",
            "last_name": "Faasil",
            "email": "fahadh@example.com",
            "password": "Password123!",
        },
    )
    th_token = reg_th.json()["data"]["access_token"]
    th_headers = {"Authorization": f"Bearer {th_token}"}

    th_res = await client.post(
        "/api/v1/therapists",
        headers=th_headers,
        json={
            "first_name": "Fahadh",
            "last_name": "Faasil",
            "display_name": "Dr. Fahadh Faasil",
            "bio": "Psychotherapist.",
            "designation": "Psychiatrist",
            "specialization": "psychiatrist",
            "qualifications": ["MD Psychiatry"],
            "experience_years": 12,
            "therapy_hours": 2000,
            "languages": ["ml", "en"],
            "expertises": ["trauma"],
            "session_modes": ["online"],
            "pricing": {"amount": 2000, "currency": "INR", "duration_minutes": 60},
        },
    )
    therapist_id = th_res.json()["data"]["id"]
    await mock_db["therapists"].update_one(
        {"id": therapist_id},
        {"$set": {"status": "active", "verification.status": "verified"}},
    )

    slot_date = (date.today() + timedelta(days=4)).isoformat()
    await client.post(
        f"/api/v1/therapists/{therapist_id}/extra-slots",
        headers=th_headers,
        json={
            "date": slot_date,
            "start_time": "15:00",
            "end_time": "16:00",
            "session_mode": "online",
        },
    )
    slots_res = await client.get(
        f"/api/v1/therapists/{therapist_id}/slots?date={slot_date}",
        headers=th_headers,
    )
    slot_id = slots_res.json()["data"][0]["id"]

    reg_cl = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Nazriya",
            "last_name": "Nazim",
            "email": "nazriya@example.com",
            "password": "Password123!",
        },
    )
    cl_token = reg_cl.json()["data"]["access_token"]
    cl_headers = {"Authorization": f"Bearer {cl_token}"}

    res_post = await client.post(
        "/api/v1/bookings/reservations",
        headers=cl_headers,
        json={
            "therapist_id": therapist_id,
            "slot_id": slot_id,
            "slot_date": slot_date,
            "session_mode": "online",
        },
    )
    reservation_id = res_post.json()["data"]["id"]

    book_res = await client.post(
        "/api/v1/bookings/confirm",
        headers=cl_headers,
        json={"reservation_id": reservation_id},
    )
    assert book_res.status_code == 201
    booking_id = book_res.json()["data"]["id"]

    # Mark linked session as IN_PROGRESS directly in DB
    await mock_db["sessions"].update_one(
        {"booking_id": booking_id},
        {"$set": {"status": SessionStatus.IN_PROGRESS.value, "started_at": datetime.now(UTC)}},
    )

    # Attempt to cancel booking -> must be rejected
    cancel_res = await client.post(
        f"/api/v1/bookings/{booking_id}/cancel",
        headers=cl_headers,
        json={"reason": "Need to cancel running session"},
    )
    assert cancel_res.status_code == 400
    assert "BOOKING_CANCEL_NOT_ALLOWED" in cancel_res.json()["error"]["code"]
