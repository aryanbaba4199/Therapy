"""Adversarial and concurrency tests for Auth refresh rotation, OTP consumption, and rate limiting."""

import asyncio
from typing import Any

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_concurrent_refresh_token_rotation_single_winner(
    client: AsyncClient, mock_db: Any
) -> None:
    """5 simultaneous refresh requests using the EXACT same refresh token. Exactly 1 must succeed."""
    # 1. Register a user
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Prithviraj",
            "last_name": "Sukumaran",
            "email": "prithvi@example.com",
            "password": "Password123!",
        },
    )
    assert reg.status_code == 201
    refresh_token = reg.json()["data"]["refresh_token"]

    # 2. Fire 5 concurrent requests with the identical refresh token
    async def do_refresh() -> int:
        res = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        return res.status_code

    results = await asyncio.gather(*(do_refresh() for _ in range(5)))

    # Exactly 1 must succeed with 200, the other 4 must fail with 401
    assert results.count(200) == 1
    assert results.count(401) == 4


@pytest.mark.asyncio
async def test_concurrent_otp_verification_atomicity(
    client: AsyncClient, mock_db: Any
) -> None:
    """Simultaneous verification of the same OTP: only one can successfully consume it."""
    phone = "+919876543210"

    # Send OTP
    send_res = await client.post(
        "/api/v1/auth/otp/send",
        json={"phone": phone, "channel": "whatsapp"},
    )
    assert send_res.status_code == 200

    # In test environment, fix the OTP code to '1234' with known hash
    from app.core.config import get_settings
    from app.modules.auth.auth_utils import hash_otp

    settings = get_settings()
    otp_code = "1234"
    known_hash = hash_otp(otp_code, settings.jwt_secret_key)
    await mock_db["auth_otps"].update_one(
        {"phone": phone},
        {"$set": {"otp_hash": known_hash, "attempts": 0}},
    )

    async def verify() -> int:
        res = await client.post(
            "/api/v1/auth/otp/verify",
            json={"phone": phone, "otp": otp_code},
        )
        return res.status_code

    # Fire 2 simultaneous verification requests
    results = await asyncio.gather(verify(), verify())

    assert results.count(200) == 1
    assert results.count(400) == 1
