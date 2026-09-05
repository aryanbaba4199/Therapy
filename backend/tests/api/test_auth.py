"""Comprehensive test suite for Authentication endpoints and lifecycle."""

from typing import Any

import pytest
from fastapi import FastAPI
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient) -> None:
    """Test standard user registration via email and password."""
    payload = {
        "first_name": "Sarah",
        "last_name": "Thomas",
        "email": "sarah.thomas@example.com",
        "phone": "+919876543210",
        "password": "SecurePassword123!",
        "language": "en",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201

    body = response.json()
    assert body["success"] is True
    assert "access_token" in body["data"]
    assert "user" in body["data"]
    assert body["data"]["user"]["email"] == "sarah.thomas@example.com"
    assert body["data"]["user"]["first_name"] == "Sarah"
    assert "password_hash" not in body["data"]["user"]


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient) -> None:
    """Test duplicate registration error handling."""
    payload = {
        "first_name": "Sarah",
        "last_name": "Thomas",
        "email": "sarah.unique@example.com",
        "password": "SecurePassword123!",
    }
    res1 = await client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = await client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 409
    assert res2.json()["error"]["code"] == "USER_EMAIL_ALREADY_EXISTS"


@pytest.mark.asyncio
async def test_register_missing_contact(client: AsyncClient) -> None:
    """Test registration fails if neither email nor phone is given."""
    payload = {
        "first_name": "Ghost",
        "last_name": "User",
        "password": "SecurePassword123!",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient) -> None:
    """Test credentials login for registered user."""
    reg_payload = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "password": "Password123!",
    }
    await client.post("/api/v1/auth/register", json=reg_payload)

    login_res = await client.post(
        "/api/v1/auth/login",
        json={"identifier": "john.doe@example.com", "password": "Password123!"},
    )
    assert login_res.status_code == 200
    data = login_res.json()["data"]
    assert "access_token" in data
    assert data["user"]["email"] == "john.doe@example.com"


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient) -> None:
    """Test login failure with invalid password."""
    reg_payload = {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.wrong@example.com",
        "password": "Password123!",
    }
    await client.post("/api/v1/auth/register", json=reg_payload)

    login_res = await client.post(
        "/api/v1/auth/login",
        json={"identifier": "john.wrong@example.com", "password": "WrongPassword!"},
    )
    assert login_res.status_code == 401
    assert login_res.json()["error"]["code"] == "AUTH_INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_otp_lifecycle_and_verification(client: AsyncClient, mock_db: Any) -> None:
    """Test dispatching and verifying OTP code."""
    phone = "+919811223344"

    # 1. Send OTP
    send_res = await client.post(
        "/api/v1/auth/otp/send",
        json={"phone": phone, "channel": "whatsapp"},
    )
    assert send_res.status_code == 200
    assert send_res.json()["data"]["phone"] == phone

    # 2. Rate limit cooldown check
    cooldown_res = await client.post(
        "/api/v1/auth/otp/send",
        json={"phone": phone, "channel": "whatsapp"},
    )
    assert cooldown_res.status_code == 429
    assert cooldown_res.json()["error"]["code"] == "AUTH_OTP_RATE_LIMITED"

    # 3. Invalid OTP attempt
    verify_bad = await client.post(
        "/api/v1/auth/otp/verify",
        json={"phone": phone, "otp": "0000"},
    )
    assert verify_bad.status_code == 400
    assert verify_bad.json()["error"]["code"] == "AUTH_INVALID_OTP"

    # 4. Extract generated OTP hash from mock_db and test correct OTP
    # For testing, we can inject a known hash or set hash to known OTP
    from app.core.config import get_settings
    from app.modules.auth.auth_utils import hash_otp

    settings = get_settings()
    known_otp = "1234"
    known_hash = hash_otp(known_otp, settings.jwt_secret_key)
    await mock_db["auth_otps"].update_one(
        {"phone": phone},
        {"$set": {"otp_hash": known_hash, "attempts": 0}},
    )

    verify_good = await client.post(
        "/api/v1/auth/otp/verify",
        json={"phone": phone, "otp": known_otp},
    )
    assert verify_good.status_code == 200
    verify_data = verify_good.json()["data"]
    assert "access_token" in verify_data
    assert verify_data["user"]["phone"] == phone


@pytest.mark.asyncio
async def test_refresh_token_rotation(client: AsyncClient) -> None:
    """Test refresh token rotation and revocation."""
    reg_payload = {
        "first_name": "Alice",
        "last_name": "Smith",
        "email": "alice.refresh@example.com",
        "password": "Password123!",
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    refresh_token = reg_res.json()["data"]["refresh_token"]

    # 1. Rotate token
    ref_res = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert ref_res.status_code == 200
    new_data = ref_res.json()["data"]
    new_refresh = new_data["refresh_token"]
    assert new_refresh != refresh_token

    # 2. Reuse of old rotated token should fail
    reuse_res = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert reuse_res.status_code == 401
    assert reuse_res.json()["error"]["code"] == "AUTH_REFRESH_TOKEN_INVALID"


@pytest.mark.asyncio
async def test_get_me_profile(client: AsyncClient) -> None:
    """Test GET /api/v1/auth/me endpoint."""
    reg_payload = {
        "first_name": "Robert",
        "last_name": "Paul",
        "email": "robert.paul@example.com",
        "password": "Password123!",
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    token = reg_res.json()["data"]["access_token"]

    # Valid token
    me_res = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    assert me_res.json()["data"]["email"] == "robert.paul@example.com"

    # Missing token
    anon_res = await client.get("/api/v1/auth/me")
    assert anon_res.status_code == 401


@pytest.mark.asyncio
async def test_logout_revocation(client: AsyncClient) -> None:
    """Test session logout and token revocation."""
    reg_payload = {
        "first_name": "Oliver",
        "last_name": "Twist",
        "email": "oliver@example.com",
        "password": "Password123!",
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    token = reg_res.json()["data"]["access_token"]
    refresh = reg_res.json()["data"]["refresh_token"]

    # Logout
    logout_res = await client.post(
        "/api/v1/auth/logout",
        headers={
            "Authorization": f"Bearer {token}",
            "Cookie": f"oppam_refresh_token={refresh}",
        },
    )
    assert logout_res.status_code == 200
    assert logout_res.json()["data"]["status"] == "logged_out"

    # Subsequent refresh attempt with revoked token should fail
    ref_res = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert ref_res.status_code == 401


@pytest.mark.asyncio
async def test_otp_max_attempts_exceeded(client: AsyncClient, mock_db: Any) -> None:
    """Test that OTP fails permanently once max attempts are reached."""
    phone = "+919111222333"
    await client.post("/api/v1/auth/otp/send", json={"phone": phone})

    # Set attempts to 5 (max)
    await mock_db["auth_otps"].update_one(
        {"phone": phone},
        {"$set": {"attempts": 5}},
    )

    verify_res = await client.post(
        "/api/v1/auth/otp/verify",
        json={"phone": phone, "otp": "1234"},
    )
    assert verify_res.status_code == 400
    assert verify_res.json()["error"]["code"] == "AUTH_OTP_MAX_ATTEMPTS"


@pytest.mark.asyncio
async def test_inactive_account_login_blocked(client: AsyncClient, mock_db: Any) -> None:
    """Test that suspended or inactive users cannot log in."""
    reg_payload = {
        "first_name": "Banned",
        "last_name": "User",
        "email": "banned@example.com",
        "password": "Password123!",
    }
    await client.post("/api/v1/auth/register", json=reg_payload)

    # Set status to suspended
    await mock_db["users"].update_one(
        {"email": "banned@example.com"},
        {"$set": {"status": "suspended"}},
    )

    login_res = await client.post(
        "/api/v1/auth/login",
        json={"identifier": "banned@example.com", "password": "Password123!"},
    )
    assert login_res.status_code == 403
    assert login_res.json()["error"]["code"] == "AUTH_ACCOUNT_INACTIVE"


@pytest.mark.asyncio
async def test_require_roles_enforcement(client: AsyncClient, app: FastAPI, mock_db: Any) -> None:
    """Test role-based access control dependency."""
    from fastapi import Depends

    from app.common.responses.api_response import ApiResponse, success_response
    from app.modules.auth.auth_dependency import require_roles
    from app.modules.user.user_constants import UserRole
    from app.modules.user.user_model import UserInDB

    # Register dynamic test route requiring ADMIN role
    @app.get("/api/v1/test-admin-only", response_model=ApiResponse[dict[str, str]])
    async def admin_only_endpoint(
        user: UserInDB = Depends(require_roles(UserRole.ADMIN)),
    ) -> ApiResponse[dict[str, str]]:
        return success_response(data={"message": "Admin granted"})

    # 1. Normal user with role USER
    reg_payload = {
        "first_name": "Standard",
        "last_name": "User",
        "email": "normal@example.com",
        "password": "Password123!",
    }
    res = await client.post("/api/v1/auth/register", json=reg_payload)
    user_token = res.json()["data"]["access_token"]

    fail_res = await client.get(
        "/api/v1/test-admin-only",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert fail_res.status_code == 403
    assert fail_res.json()["error"]["code"] == "FORBIDDEN"

    # 2. Promote user to ADMIN in mock_db
    await mock_db["users"].update_one(
        {"email": "normal@example.com"},
        {"$set": {"roles": ["admin"]}},
    )

    pass_res = await client.get(
        "/api/v1/test-admin-only",
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert pass_res.status_code == 200
    assert pass_res.json()["data"]["message"] == "Admin granted"
