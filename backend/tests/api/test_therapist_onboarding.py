"""Comprehensive tests for Super Admin -> Therapist Onboarding workflow."""

import asyncio
from typing import Any

import pytest
from httpx import AsyncClient

from app.modules.therapist.therapist_constants import (
    SessionMode,
    TherapistSpecialization,
    TherapistStatus,
    TherapistVerificationStatus,
)


async def create_user_and_login(
    client: AsyncClient,
    mock_db: Any,
    email: str,
    password: str = "Password123!",
    roles: list[str] | None = None,
) -> tuple[str, str, dict[str, str]]:
    """Helper to create a user with specified roles and return user_id, token, headers."""
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Test",
            "last_name": "User",
            "email": email,
            "password": password,
        },
    )
    assert reg.status_code in (200, 201)
    user_id = reg.json()["data"]["user"]["id"]
    token = reg.json()["data"]["access_token"]
    if roles:
        await mock_db["users"].update_one(
            {"id": user_id},
            {"$set": {"roles": roles}},
        )
    return user_id, token, {"Authorization": f"Bearer {token}"}


def sample_onboard_payload(
    email: str = "practitioner@example.com",
    phone: str = "+919876543210",
    status: str = "draft",
    verification_status: str = "pending",
    include_availability: bool = True,
) -> dict[str, Any]:
    """Helper returning a valid OnboardTherapistRequest dictionary."""
    payload: dict[str, Any] = {
        "account": {
            "first_name": "Ananya",
            "last_name": "Menon",
            "email": email,
            "phone": phone,
            "temporary_password": "TempPassword123!",
        },
        "profile": {
            "display_name": "Dr. Ananya Menon",
            "bio": "Experienced consultant clinical psychologist specializing in trauma and anxiety disorders.",
            "designation": "Senior Clinical Psychologist",
            "specialization": TherapistSpecialization.CLINICAL_PSYCHOLOGIST.value,
            "qualifications": ["M.Phil Clinical Psychology", "Ph.D Psychology"],
            "experience_years": 8,
            "therapy_hours": 1200,
            "languages": ["English", "Malayalam", "Tamil"],
            "expertises": ["CBT", "Trauma", "Anxiety"],
            "session_modes": [SessionMode.ONLINE.value, SessionMode.OFFLINE_KOZHIKODE.value],
            "profile_image_url": "https://example.com/avatar.jpg",
        },
        "pricing": {
            "amount": 1800.0,
            "currency": "INR",
            "duration_minutes": 50,
        },
        "verification": {
            "status": verification_status,
            "registration_number": "RCI-CR-2018-9999",
            "registration_authority": "Rehabilitation Council of India",
        },
        "status": status,
    }
    if include_availability:
        payload["availability"] = {
            "timezone": "Asia/Kolkata",
            "days": [
                {
                    "day_of_week": 1,
                    "intervals": [
                        {
                            "start_time": "10:00",
                            "end_time": "13:00",
                            "session_modes": [SessionMode.ONLINE.value],
                        },
                        {
                            "start_time": "14:00",
                            "end_time": "17:00",
                            "session_modes": [SessionMode.ONLINE.value],
                        },
                    ],
                },
                {
                    "day_of_week": 3,
                    "intervals": [
                        {
                            "start_time": "11:00",
                            "end_time": "15:00",
                            "session_modes": [SessionMode.ONLINE.value],
                        }
                    ],
                },
            ],
        }
    return payload


@pytest.mark.asyncio
async def test_onboard_therapist_super_admin_success_draft(
    client: AsyncClient, mock_db: Any
) -> None:
    """Super Admin onboards therapist in DRAFT status with credentials and schedule."""
    _, _, admin_headers = await create_user_and_login(
        client, mock_db, "superadmin@example.com", roles=["super_admin", "admin", "user"]
    )

    payload = sample_onboard_payload(
        email="dr.ananya@example.com",
        phone="+919876543211",
        status=TherapistStatus.DRAFT.value,
        verification_status=TherapistVerificationStatus.PENDING.value,
        include_availability=True,
    )

    resp = await client.post(
        "/api/v1/operations/therapists/onboard",
        json=payload,
        headers=admin_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]

    assert data["email"] == "dr.ananya@example.com"
    assert data["phone"] == "+919876543211"
    assert data["temporary_password"] == "TempPassword123!"
    assert data["status"] == "draft"
    assert data["verification_status"] == "pending"
    assert data["schedule_configured"] is True

    user_doc = await mock_db["users"].find_one({"id": data["user_id"]})
    assert user_doc is not None
    assert user_doc["roles"] == ["therapist"]
    assert user_doc["is_verified"] is True

    therapist_doc = await mock_db["therapists"].find_one({"user_id": data["user_id"]})
    assert therapist_doc is not None
    assert therapist_doc["display_name"] == "Dr. Ananya Menon"
    assert therapist_doc["pricing"]["amount"] == 1800.0

    audit_doc = await mock_db["audit_logs"].find_one({"action": "therapist_created"})
    assert audit_doc is not None
    assert audit_doc["resource_id"] == therapist_doc["id"]


@pytest.mark.asyncio
async def test_onboard_therapist_super_admin_active_and_verified(
    client: AsyncClient, mock_db: Any
) -> None:
    """Super Admin onboards therapist directly into ACTIVE + VERIFIED status."""
    _, _, admin_headers = await create_user_and_login(
        client, mock_db, "superadmin2@example.com", roles=["super_admin", "admin"]
    )

    payload = sample_onboard_payload(
        email="dr.active@example.com",
        phone="+919876543212",
        status=TherapistStatus.ACTIVE.value,
        verification_status=TherapistVerificationStatus.VERIFIED.value,
        include_availability=True,
    )

    resp = await client.post(
        "/api/v1/operations/therapists/onboard",
        json=payload,
        headers=admin_headers,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["status"] == "active"
    assert data["verification_status"] == "verified"

    discovery_resp = await client.get("/api/v1/therapists")
    assert discovery_resp.status_code == 200
    therapists = discovery_resp.json()["data"]["items"]
    found = any(t["id"] == data["therapist"]["id"] for t in therapists)
    assert found is True


@pytest.mark.asyncio
async def test_onboard_therapist_active_without_verification_rejected(
    client: AsyncClient, mock_db: Any
) -> None:
    """Attempting to activate an unverified therapist during onboarding must be rejected."""
    _, _, admin_headers = await create_user_and_login(
        client, mock_db, "superadmin3@example.com", roles=["super_admin"]
    )

    payload = sample_onboard_payload(
        email="dr.unverified@example.com",
        phone="+919876543213",
        status=TherapistStatus.ACTIVE.value,
        verification_status=TherapistVerificationStatus.PENDING.value,
    )

    resp = await client.post(
        "/api/v1/operations/therapists/onboard",
        json=payload,
        headers=admin_headers,
    )
    assert resp.status_code == 400
    assert resp.json()["error"]["code"] == "THERAPIST_VERIFICATION_REQUIRED"


@pytest.mark.asyncio
async def test_onboard_therapist_forbidden_for_regular_users(
    client: AsyncClient, mock_db: Any
) -> None:
    """Non-admin callers cannot access the onboarding endpoint."""
    _, _, user_headers = await create_user_and_login(
        client, mock_db, "normaluser@example.com", roles=["user"]
    )

    payload = sample_onboard_payload(
        email="dr.illegal@example.com",
        phone="+919876543214",
    )

    resp = await client.post(
        "/api/v1/operations/therapists/onboard",
        json=payload,
        headers=user_headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_onboard_therapist_duplicate_email_or_phone_conflict(
    client: AsyncClient, mock_db: Any
) -> None:
    """Collision detection prevents creating therapists with already registered email or phone."""
    _, _, admin_headers = await create_user_and_login(
        client, mock_db, "superadmin4@example.com", roles=["super_admin"]
    )

    payload1 = sample_onboard_payload(
        email="dr.duplicate@example.com",
        phone="+919876543215",
    )
    resp1 = await client.post(
        "/api/v1/operations/therapists/onboard",
        json=payload1,
        headers=admin_headers,
    )
    assert resp1.status_code == 200

    payload_dup_email = sample_onboard_payload(
        email="dr.duplicate@example.com",
        phone="+919876543216",
    )
    resp2 = await client.post(
        "/api/v1/operations/therapists/onboard",
        json=payload_dup_email,
        headers=admin_headers,
    )
    assert resp2.status_code == 400
    assert resp2.json()["error"]["code"] == "USER_EMAIL_ALREADY_EXISTS"

    payload_dup_phone = sample_onboard_payload(
        email="dr.diff@example.com",
        phone="+919876543215",
    )
    resp3 = await client.post(
        "/api/v1/operations/therapists/onboard",
        json=payload_dup_phone,
        headers=admin_headers,
    )
    assert resp3.status_code == 400
    assert resp3.json()["error"]["code"] == "USER_PHONE_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_onboard_therapist_adversarial_concurrency(
    client: AsyncClient, mock_db: Any
) -> None:
    """20 concurrent onboarding requests with identical email/phone -> exactly 1 succeeds."""
    _, _, admin_headers = await create_user_and_login(
        client, mock_db, "superadmin_concurrent@example.com", roles=["super_admin"]
    )

    payload = sample_onboard_payload(
        email="dr.concurrent@example.com",
        phone="+919876543299",
    )

    tasks = [
        client.post(
            "/api/v1/operations/therapists/onboard",
            json=payload,
            headers=admin_headers,
        )
        for _ in range(20)
    ]

    responses = await asyncio.gather(*tasks)
    successes = [r for r in responses if r.status_code == 200]
    failures = [r for r in responses if r.status_code in (400, 409)]

    assert len(successes) == 1, f"Expected 1 success, got {len(successes)}"
    assert len(failures) == 19
