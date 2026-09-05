"""Concurrency tests for Booking & Reservation engine."""

import asyncio
from datetime import date, timedelta
from typing import Any

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_concurrent_reservations_only_one_succeeds(
    client: AsyncClient, mock_db: Any
) -> None:
    """Simulate 5 concurrent reservation requests for the exact same slot. Exactly one must succeed and the others receive 409 Conflict."""
    # 1. Register therapist
    reg_th = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Mammootty",
            "last_name": "Panicker",
            "email": "mammootty@example.com",
            "password": "Password123!",
        },
    )
    th_token = reg_th.json()["data"]["access_token"]
    th_headers = {"Authorization": f"Bearer {th_token}"}

    th_res = await client.post(
        "/api/v1/therapists",
        headers=th_headers,
        json={
            "first_name": "Mammootty",
            "last_name": "Panicker",
            "display_name": "Dr. Mammootty Panicker",
            "bio": "Senior behavioral psychologist.",
            "designation": "Clinical Psychologist",
            "specialization": "clinical_psychologist",
            "qualifications": ["Ph.D Psychology"],
            "experience_years": 15,
            "therapy_hours": 3000,
            "languages": ["ml", "en"],
            "expertises": ["stress", "career"],
            "session_modes": ["online"],
            "pricing": {"amount": 1500, "currency": "INR", "duration_minutes": 60},
        },
    )
    therapist_id = th_res.json()["data"]["id"]

    await mock_db["therapists"].update_one(
        {"id": therapist_id},
        {"$set": {"status": "active", "verification.status": "verified"}},
    )

    slot_date = (date.today() + timedelta(days=2)).isoformat()
    extra_res = await client.post(
        f"/api/v1/therapists/{therapist_id}/extra-slots",
        headers=th_headers,
        json={
            "date": slot_date,
            "start_time": "14:00",
            "end_time": "15:00",
            "session_mode": "online",
        },
    )
    assert extra_res.status_code == 200

    slots_res = await client.get(
        f"/api/v1/therapists/{therapist_id}/slots?date={slot_date}",
        headers=th_headers,
    )
    assert slots_res.status_code == 200
    slot_id = slots_res.json()["data"][0]["id"]

    # 2. Register 5 different clients
    client_tokens: list[str] = []
    for i in range(5):
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "first_name": f"Client{i}",
                "last_name": "Test",
                "email": f"client{i}.concurrent@example.com",
                "password": "Password123!",
            },
        )
        client_tokens.append(reg.json()["data"]["access_token"])

    # 3. Fire concurrent reservation attempts simultaneously
    payload = {
        "therapist_id": therapist_id,
        "slot_id": slot_id,
        "slot_date": slot_date,
        "session_mode": "online",
    }

    async def attempt_reserve(token: str) -> int:
        res = await client.post(
            "/api/v1/bookings/reservations",
            headers={"Authorization": f"Bearer {token}"},
            json=payload,
        )
        return res.status_code

    statuses = await asyncio.gather(*[attempt_reserve(tok) for tok in client_tokens])

    # Exactly one request must be 201 Created, and the rest 409 Conflict
    assert statuses.count(201) == 1
    assert statuses.count(409) == 4
