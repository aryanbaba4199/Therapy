"""Comprehensive API tests for Therapist Availability and Slot Discovery."""

from datetime import date, timedelta
from typing import Any

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_set_and_get_weekly_schedule(client: AsyncClient, mock_db: Any) -> None:
    """Test authenticated therapist setting, retrieving, and validating weekly schedules."""
    # 1. Register therapist user
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Deepa",
            "last_name": "Menon",
            "email": "deepa.menon@example.com",
            "password": "Password123!",
        },
    )
    token = reg_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create therapist profile with all required fields
    th_res = await client.post(
        "/api/v1/therapists",
        headers=headers,
        json={
            "first_name": "Deepa",
            "last_name": "Menon",
            "display_name": "Dr. Deepa Menon",
            "bio": "Expert in counseling psychology with clinical experience.",
            "designation": "Consultant Psychologist",
            "specialization": "consultant_psychologist",
            "qualifications": ["M.Sc Psychology", "M.Phil"],
            "experience_years": 8,
            "therapy_hours": 1200,
            "languages": ["ml", "en"],
            "expertises": ["anxiety", "stress"],
            "session_modes": ["online"],
            "pricing": {"amount": 1000, "currency": "INR", "duration_minutes": 60},
        },
    )
    assert th_res.status_code == 201
    therapist_id = th_res.json()["data"]["id"]

    # 3. Another user cannot modify schedule (403 Forbidden)
    other_res = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Stranger",
            "last_name": "User",
            "email": "stranger@example.com",
            "password": "Password123!",
        },
    )
    stranger_token = other_res.json()["data"]["access_token"]
    stranger_headers = {"Authorization": f"Bearer {stranger_token}"}

    unauth_sched = await client.post(
        f"/api/v1/therapists/{therapist_id}/availability",
        headers=stranger_headers,
        json={
            "timezone": "Asia/Kolkata",
            "days": [
                {
                    "day_of_week": 0,
                    "intervals": [
                        {"start_time": "09:00", "end_time": "12:00", "session_modes": ["online"]}
                    ],
                }
            ],
        },
    )
    assert unauth_sched.status_code == 403
    assert unauth_sched.json()["error"]["code"] == "THERAPIST_ACCESS_DENIED"

    # 4. Valid schedule setting by owner
    sched_payload = {
        "timezone": "Asia/Kolkata",
        "days": [
            {
                "day_of_week": 0,  # Monday
                "intervals": [
                    {"start_time": "09:00", "end_time": "12:00", "session_modes": ["online"]},
                    {"start_time": "14:00", "end_time": "17:00", "session_modes": ["online"]},
                ],
            },
            {
                "day_of_week": 1,  # Tuesday
                "intervals": [
                    {"start_time": "10:00", "end_time": "14:00", "session_modes": ["online"]},
                ],
            },
        ],
    }
    set_res = await client.post(
        f"/api/v1/therapists/{therapist_id}/availability",
        headers=headers,
        json=sched_payload,
    )
    assert set_res.status_code == 200
    assert set_res.json()["data"]["therapist_id"] == therapist_id
    assert len(set_res.json()["data"]["days"]) == 2

    # 5. Overlapping intervals on same day reject with 422 Unprocessable Entity
    overlap_payload = {
        "timezone": "Asia/Kolkata",
        "days": [
            {
                "day_of_week": 0,
                "intervals": [
                    {"start_time": "09:00", "end_time": "13:00", "session_modes": ["online"]},
                    {"start_time": "12:00", "end_time": "15:00", "session_modes": ["online"]},
                ],
            }
        ],
    }
    overlap_res = await client.post(
        f"/api/v1/therapists/{therapist_id}/availability",
        headers=headers,
        json=overlap_payload,
    )
    assert overlap_res.status_code == 422

    # 6. Retrieve availability composite
    avail_res = await client.get(f"/api/v1/therapists/{therapist_id}/availability")
    assert avail_res.status_code == 200
    assert avail_res.json()["data"]["therapist_id"] == therapist_id
    assert avail_res.json()["data"]["schedule"]["timezone"] == "Asia/Kolkata"


@pytest.mark.asyncio
async def test_date_exceptions_and_extra_slots(client: AsyncClient, mock_db: Any) -> None:
    """Test date exceptions and extra slot management."""
    # 1. Register therapist user
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Rohan",
            "last_name": "Verma",
            "email": "rohan.verma@example.com",
            "password": "Password123!",
        },
    )
    token = reg_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    th_res = await client.post(
        "/api/v1/therapists",
        headers=headers,
        json={
            "first_name": "Rohan",
            "last_name": "Verma",
            "display_name": "Dr. Rohan Verma",
            "bio": "Clinical psychologist specialized in CBT and mindfulness.",
            "designation": "Consultant",
            "specialization": "clinical_psychologist",
            "qualifications": ["PsyD"],
            "experience_years": 5,
            "therapy_hours": 900,
            "languages": ["en"],
            "expertises": ["anxiety"],
            "session_modes": ["online"],
            "pricing": {"amount": 1500, "currency": "INR", "duration_minutes": 60},
        },
    )
    assert th_res.status_code == 201
    therapist_id = th_res.json()["data"]["id"]

    # 2. Add holiday date exception
    future_date = (date.today() + timedelta(days=5)).isoformat()
    exc_res = await client.post(
        f"/api/v1/therapists/{therapist_id}/availability/exceptions",
        headers=headers,
        json={
            "date": future_date,
            "is_unavailable": True,
            "reason": "Personal Leave",
        },
    )
    assert exc_res.status_code == 200
    assert exc_res.json()["data"]["date"] == future_date
    assert exc_res.json()["data"]["is_unavailable"] is True

    # 3. Add extra slot for future date
    extra_slot_date = (date.today() + timedelta(days=6)).isoformat()
    extra_res = await client.post(
        f"/api/v1/therapists/{therapist_id}/extra-slots",
        headers=headers,
        json={
            "date": extra_slot_date,
            "start_time": "19:00",
            "end_time": "20:00",
            "session_mode": "online",
        },
    )
    assert extra_res.status_code == 200
    slot_id = extra_res.json()["data"]["id"]
    assert extra_res.json()["data"]["date"] == extra_slot_date

    # 4. Duplicate/overlapping extra slot rejected (409 Conflict)
    dup_extra = await client.post(
        f"/api/v1/therapists/{therapist_id}/extra-slots",
        headers=headers,
        json={
            "date": extra_slot_date,
            "start_time": "19:30",
            "end_time": "20:30",
            "session_mode": "online",
        },
    )
    assert dup_extra.status_code == 409
    assert dup_extra.json()["error"]["code"] == "EXTRA_SLOT_CONFLICT"

    # 5. Extra slot for past date rejected (400 Bad Request)
    past_date = (date.today() - timedelta(days=1)).isoformat()
    past_extra = await client.post(
        f"/api/v1/therapists/{therapist_id}/extra-slots",
        headers=headers,
        json={
            "date": past_date,
            "start_time": "10:00",
            "end_time": "11:00",
            "session_mode": "online",
        },
    )
    assert past_extra.status_code == 400
    assert past_extra.json()["error"]["code"] == "DATE_IN_PAST"

    # 6. Delete extra slot
    del_res = await client.delete(
        f"/api/v1/therapists/{therapist_id}/extra-slots/{slot_id}",
        headers=headers,
    )
    assert del_res.status_code == 200


@pytest.mark.asyncio
async def test_public_slot_discovery_api(client: AsyncClient, mock_db: Any) -> None:
    """Test public slot discovery endpoint with verified therapist and filters."""
    # 1. Create and verify a therapist directly in database
    therapist_doc = {
        "id": "th-disc-1",
        "user_id": "user-disc-1",
        "first_name": "Meera",
        "last_name": "Nambiar",
        "display_name": "Dr. Meera Nambiar",
        "bio": "Experienced therapist",
        "designation": "Clinical Psychologist",
        "specialization": "clinical_psychologist",
        "qualifications": ["PhD"],
        "experience_years": 10,
        "therapy_hours": 2000,
        "languages": ["ml", "en"],
        "expertises": ["anxiety"],
        "session_modes": ["online"],
        "pricing": {"amount": 1000, "currency": "INR", "duration_minutes": 60},
        "status": "active",
        "verification": {"status": "verified"},
    }
    await mock_db["therapists"].insert_one(therapist_doc)

    # 2. Set weekly schedule for all 7 days: 10:00 to 12:00
    schedule_doc = {
        "id": "sched-disc-1",
        "therapist_id": "th-disc-1",
        "timezone": "Asia/Kolkata",
        "days": [
            {
                "day_of_week": d,
                "intervals": [
                    {"start_time": "10:00", "end_time": "12:00", "session_modes": ["online"]}
                ],
            }
            for d in range(7)
        ],
    }
    await mock_db["availability_schedules"].insert_one(schedule_doc)

    # 3. Add date exception for date 3 days from now
    exception_date = (date.today() + timedelta(days=3)).isoformat()
    exc_doc = {
        "id": "exc-disc-1",
        "therapist_id": "th-disc-1",
        "date": exception_date,
        "is_unavailable": True,
        "custom_intervals": [],
        "reason": "Conference",
    }
    await mock_db["availability_exceptions"].insert_one(exc_doc)

    # 4. Add extra slot for that exact unavailable date (20:00 - 21:00)
    extra_doc = {
        "id": "extra-disc-1",
        "therapist_id": "th-disc-1",
        "date": exception_date,
        "start_time": "20:00",
        "end_time": "21:00",
        "session_mode": "online",
        "status": "available",
    }
    await mock_db["extra_slots"].insert_one(extra_doc)

    # 5. Query discovery for that exception date
    res = await client.get(f"/api/v1/therapists/th-disc-1/slots?date={exception_date}")
    assert res.status_code == 200
    slots = res.json()["data"]
    # Regular 10:00-12:00 slots are suppressed; only the extra slot 20:00-21:00 is returned!
    assert len(slots) == 1
    assert slots[0]["session_mode"] == "online"

    # 6. Unbounded date range > 30 days is rejected
    start_d = date.today().isoformat()
    end_d = (date.today() + timedelta(days=40)).isoformat()
    range_res = await client.get(
        f"/api/v1/therapists/th-disc-1/slots?start_date={start_d}&end_date={end_d}"
    )
    assert range_res.status_code == 400
    assert range_res.json()["error"]["code"] == "INVALID_DATE_RANGE"
