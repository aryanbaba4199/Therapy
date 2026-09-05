"""Integration and unit API tests for Package catalog and balances."""

from typing import Any

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_package_lifecycle(client: AsyncClient, mock_db: Any) -> None:
    # 1. Register admin and user
    admin_reg = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Pkg",
            "last_name": "Admin",
            "email": "pkg.admin@example.com",
            "password": "Password123!",
        },
    )
    admin_id = admin_reg.json()["data"]["user"]["id"]
    admin_token = admin_reg.json()["data"]["access_token"]
    await mock_db["users"].update_one({"id": admin_id}, {"$set": {"roles": ["admin"]}})

    user_reg = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Client",
            "last_name": "Package",
            "email": "client.pkg@example.com",
            "password": "Password123!",
        },
    )
    _user_id = user_reg.json()["data"]["user"]["id"]
    user_token = user_reg.json()["data"]["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Admin creates a package product (e.g. 5 Sessions Bundle)
    prod_res = await client.post(
        "/api/v1/packages",
        headers=admin_headers,
        json={
            "title": "5 Sessions Wellness Bundle",
            "description": "Save on 5 full counselling sessions",
            "session_count": 5,
            "validity_days": 90,
            "price_minor": 450000,  # ₹4500 (₹900/session)
        },
    )
    assert prod_res.status_code == 201
    prod = prod_res.json()["data"]
    prod_id = prod["id"]
    assert prod["session_count"] == 5

    # 3. User lists public packages
    list_res = await client.get("/api/v1/packages", headers=user_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()["data"]) >= 1

    # 4. User views single package
    get_res = await client.get(f"/api/v1/packages/{prod_id}", headers=user_headers)
    assert get_res.status_code == 200
    assert get_res.json()["data"]["id"] == prod_id

    # 5. User checks their own packages (empty initially)
    my_pkgs = await client.get("/api/v1/packages/my", headers=user_headers)
    assert my_pkgs.status_code == 200
    assert len(my_pkgs.json()["data"]) == 0
