"""Test suite for User profile endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_user_profile_crud(client: AsyncClient) -> None:
    """Test retrieving and updating user profile."""
    reg_payload = {
        "first_name": "Maya",
        "last_name": "Menon",
        "email": "maya.menon@example.com",
        "phone": "+919988776655",
        "password": "Password123!",
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    token = reg_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Fetch profile
    get_res = await client.get("/api/v1/users/me", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["data"]["first_name"] == "Maya"
    assert get_res.json()["data"]["last_name"] == "Menon"

    # 2. Update profile
    patch_res = await client.patch(
        "/api/v1/users/me",
        headers=headers,
        json={
            "first_name": "Mayamol",
            "preferences": {"language": "ml", "notifications": False},
        },
    )
    assert patch_res.status_code == 200
    data = patch_res.json()["data"]
    assert data["first_name"] == "Mayamol"
    assert data["last_name"] == "Menon"
    assert data["preferences"]["language"] == "ml"
    assert data["preferences"]["notifications"] is False

    # 3. Unauthorized access
    anon_res = await client.get("/api/v1/users/me")
    assert anon_res.status_code == 401
