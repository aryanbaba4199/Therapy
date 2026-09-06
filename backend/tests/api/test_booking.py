"""Comprehensive integration and API tests for Booking & Reservation engine."""

from datetime import date, timedelta
from typing import Any

import pytest
from httpx import AsyncClient


async def _setup_therapist_and_slot(client: AsyncClient, mock_db: Any) -> tuple[str, str, str, str]:
    """Helper to create an active therapist, verified, and return therapist_id, slot_id, slot_date, therapist_token."""
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Suresh",
            "last_name": "Gopi",
            "email": f"suresh.{date.today().isoformat()}@example.com",
            "password": "Password123!",
        },
    )
    th_token = reg_res.json()["data"]["access_token"]
    th_headers = {"Authorization": f"Bearer {th_token}"}

    th_res = await client.post(
        "/api/v1/therapists",
        headers=th_headers,
        json={
            "first_name": "Suresh",
            "last_name": "Gopi",
            "display_name": "Dr. Suresh Gopi",
            "bio": "Experienced clinical psychologist in Kochi.",
            "designation": "Clinical Psychologist",
            "specialization": "clinical_psychologist",
            "qualifications": ["Ph.D Psychology"],
            "experience_years": 10,
            "therapy_hours": 2000,
            "languages": ["ml", "en"],
            "expertises": ["depression", "trauma"],
            "session_modes": ["online"],
            "pricing": {"amount": 1200, "currency": "INR", "duration_minutes": 60},
        },
    )
    therapist_id = th_res.json()["data"]["id"]

    await mock_db["therapists"].update_one(
        {"id": therapist_id},
        {"$set": {"status": "active", "verification.status": "verified"}},
    )

    tomorrow = date.today() + timedelta(days=1)
    tomorrow_str = tomorrow.isoformat()

    extra_res = await client.post(
        f"/api/v1/therapists/{therapist_id}/extra-slots",
        headers=th_headers,
        json={
            "date": tomorrow_str,
            "start_time": "10:00",
            "end_time": "11:00",
            "session_mode": "online",
        },
    )
    assert extra_res.status_code == 200

    slots_res = await client.get(
        f"/api/v1/therapists/{therapist_id}/slots?date={tomorrow_str}",
        headers=th_headers,
    )
    assert slots_res.status_code == 200
    slots = slots_res.json()["data"]
    assert len(slots) >= 1
    slot_id = slots[0]["id"]

    return therapist_id, slot_id, tomorrow_str, th_token


@pytest.mark.asyncio
async def test_create_and_get_reservation(client: AsyncClient, mock_db: Any) -> None:
    """Test authenticated client reserving a slot and viewing the reservation."""
    therapist_id, slot_id, slot_date, _ = await _setup_therapist_and_slot(client, mock_db)

    reg_client = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Rahul",
            "last_name": "Nair",
            "email": "rahul.nair@example.com",
            "password": "Password123!",
        },
    )
    client_token = reg_client.json()["data"]["access_token"]
    client_headers = {"Authorization": f"Bearer {client_token}"}

    res_payload = {
        "therapist_id": therapist_id,
        "slot_id": slot_id,
        "slot_date": slot_date,
        "session_mode": "online",
    }
    create_res = await client.post(
        "/api/v1/bookings/reservations",
        headers=client_headers,
        json=res_payload,
    )
    assert create_res.status_code == 201
    res_data = create_res.json()["data"]
    assert res_data["therapist_id"] == therapist_id
    assert res_data["slot_id"] == slot_id
    assert res_data["status"] == "active"
    assert res_data["seconds_remaining"] > 0
    reservation_id = res_data["id"]

    get_res = await client.get(
        f"/api/v1/bookings/reservations/{reservation_id}",
        headers=client_headers,
    )
    assert get_res.status_code == 200
    assert get_res.json()["data"]["id"] == reservation_id

    other_client = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Other",
            "last_name": "User",
            "email": "other.user@example.com",
            "password": "Password123!",
        },
    )
    other_headers = {"Authorization": f"Bearer {other_client.json()['data']['access_token']}"}

    conflict_res = await client.post(
        "/api/v1/bookings/reservations",
        headers=other_headers,
        json=res_payload,
    )
    assert conflict_res.status_code == 409
    assert conflict_res.json()["error"]["code"] == "BOOKING_SLOT_UNAVAILABLE"


@pytest.mark.asyncio
async def test_cancel_reservation_releases_slot(client: AsyncClient, mock_db: Any) -> None:
    """Test that cancelling a reservation releases the slot immediately for another client."""
    therapist_id, slot_id, slot_date, _ = await _setup_therapist_and_slot(client, mock_db)

    reg_client1 = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "User1",
            "last_name": "One",
            "email": "user1@example.com",
            "password": "Password123!",
        },
    )
    headers1 = {"Authorization": f"Bearer {reg_client1.json()['data']['access_token']}"}

    res_payload = {
        "therapist_id": therapist_id,
        "slot_id": slot_id,
        "slot_date": slot_date,
        "session_mode": "online",
    }
    create_res = await client.post(
        "/api/v1/bookings/reservations",
        headers=headers1,
        json=res_payload,
    )
    assert create_res.status_code == 201
    reservation_id = create_res.json()["data"]["id"]

    del_res = await client.delete(
        f"/api/v1/bookings/reservations/{reservation_id}",
        headers=headers1,
    )
    assert del_res.status_code == 200

    reg_client2 = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "User2",
            "last_name": "Two",
            "email": "user2@example.com",
            "password": "Password123!",
        },
    )
    headers2 = {"Authorization": f"Bearer {reg_client2.json()['data']['access_token']}"}

    create_res2 = await client.post(
        "/api/v1/bookings/reservations",
        headers=headers2,
        json=res_payload,
    )
    assert create_res2.status_code == 201
    assert create_res2.json()["data"]["slot_id"] == slot_id


@pytest.mark.asyncio
async def test_confirm_booking_and_idempotency(client: AsyncClient, mock_db: Any) -> None:
    """Test confirming a reservation into a booking and verify idempotency."""
    therapist_id, slot_id, slot_date, _ = await _setup_therapist_and_slot(client, mock_db)

    reg_client = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Ananya",
            "last_name": "Pillai",
            "email": "ananya.pillai@example.com",
            "password": "Password123!",
        },
    )
    client_token = reg_client.json()["data"]["access_token"]
    client_headers = {"Authorization": f"Bearer {client_token}"}

    create_res = await client.post(
        "/api/v1/bookings/reservations",
        headers=client_headers,
        json={
            "therapist_id": therapist_id,
            "slot_id": slot_id,
            "slot_date": slot_date,
            "session_mode": "online",
        },
    )
    assert create_res.status_code == 201
    reservation_id = create_res.json()["data"]["id"]

    confirm_payload = {
        "reservation_id": reservation_id,
        "client_notes": "First time seeking therapy.",
    }
    confirm_res = await client.post(
        "/api/v1/bookings/confirm",
        headers=client_headers,
        json=confirm_payload,
    )
    assert confirm_res.status_code == 201
    booking_data = confirm_res.json()["data"]
    assert booking_data["id"] is not None
    assert booking_data["status"] == "confirmed"
    assert booking_data["pricing"]["amount"] == 1200
    assert booking_data["therapist"]["display_name"] == "Dr. Suresh Gopi"
    assert booking_data.get("session_id") is not None
    assert booking_data.get("meeting") is not None
    assert booking_data["meeting"]["status"] == "ready"
    assert "meet.google.com" in booking_data["meeting"]["join_url"]
    booking_id = booking_data["id"]

    # Verify lookup by reservation_id succeeds and includes meeting
    res_lookup = await client.get(f"/api/v1/bookings/{reservation_id}", headers=client_headers)
    assert res_lookup.status_code == 200
    assert res_lookup.json()["data"]["id"] == booking_id
    assert res_lookup.json()["data"]["meeting"]["status"] == "ready"

    # Verify lookup by booking_id succeeds and includes meeting
    book_lookup = await client.get(f"/api/v1/bookings/{booking_id}", headers=client_headers)
    assert book_lookup.status_code == 200
    assert book_lookup.json()["data"]["id"] == booking_id
    assert book_lookup.json()["data"]["meeting"]["status"] == "ready"

    confirm_again = await client.post(
        "/api/v1/bookings/confirm",
        headers=client_headers,
        json=confirm_payload,
    )
    assert confirm_again.status_code in (200, 201)
    assert confirm_again.json()["data"]["id"] == booking_id
    assert confirm_again.json()["data"]["meeting"] is not None

    slots_res = await client.get(
        f"/api/v1/therapists/{therapist_id}/slots?date={slot_date}",
        headers=client_headers,
    )
    avail_slot_ids = [s["id"] for s in slots_res.json()["data"]]
    assert slot_id not in avail_slot_ids


@pytest.mark.asyncio
async def test_list_and_cancel_booking(client: AsyncClient, mock_db: Any) -> None:
    """Test listing client bookings and cancelling a confirmed booking."""
    therapist_id, slot_id, slot_date, _ = await _setup_therapist_and_slot(client, mock_db)

    reg_client = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Meera",
            "last_name": "Krishnan",
            "email": "meera.krishnan@example.com",
            "password": "Password123!",
        },
    )
    client_token = reg_client.json()["data"]["access_token"]
    client_headers = {"Authorization": f"Bearer {client_token}"}

    create_res = await client.post(
        "/api/v1/bookings/reservations",
        headers=client_headers,
        json={
            "therapist_id": therapist_id,
            "slot_id": slot_id,
            "slot_date": slot_date,
            "session_mode": "online",
        },
    )
    reservation_id = create_res.json()["data"]["id"]

    confirm_res = await client.post(
        "/api/v1/bookings/confirm",
        headers=client_headers,
        json={"reservation_id": reservation_id},
    )
    booking_id = confirm_res.json()["data"]["id"]

    list_res = await client.get(
        "/api/v1/bookings",
        headers=client_headers,
    )
    assert list_res.status_code == 200
    items = list_res.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["id"] == booking_id

    list_upcoming = await client.get(
        "/api/v1/bookings?filter=upcoming",
        headers=client_headers,
    )
    assert list_upcoming.status_code == 200
    assert len(list_upcoming.json()["data"]["items"]) == 1

    cancel_res = await client.post(
        f"/api/v1/bookings/{booking_id}/cancel",
        headers=client_headers,
        json={"reason": "Scheduling conflict."},
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["data"]["status"] == "cancelled"
    assert cancel_res.json()["data"]["cancellation_reason"] == "Scheduling conflict."

    cancel_again = await client.post(
        f"/api/v1/bookings/{booking_id}/cancel",
        headers=client_headers,
        json={"reason": "Try again"},
    )
    assert cancel_again.status_code == 400
    assert cancel_again.json()["error"]["code"] == "BOOKING_CANCEL_NOT_ALLOWED"
