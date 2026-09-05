"""Integration and unit API tests for Offer and Coupon management."""

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_offer_lifecycle_and_validation(client: AsyncClient, mock_db: Any) -> None:
    # 1. Register admin and regular user
    admin_reg = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Offer",
            "last_name": "Admin",
            "email": "offer.admin@example.com",
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
            "last_name": "User",
            "email": "client.offer@example.com",
            "password": "Password123!",
        },
    )
    user_token = user_reg.json()["data"]["access_token"]
    user_headers = {"Authorization": f"Bearer {user_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 2. Create a percentage offer with admin
    now = datetime.now(UTC)
    valid_from = now - timedelta(days=1)
    valid_until = now + timedelta(days=10)

    create_res = await client.post(
        "/api/v1/offers",
        headers=admin_headers,
        json={
            "code": "WELCOME20",
            "title": "Welcome 20% Off",
            "description": "Get 20% off your therapy session",
            "discount_type": "percentage",
            "discount_value": 20,
            "min_order_minor": 50000,  # ₹500
            "max_discount_minor": 30000,  # ₹300 cap
            "valid_from": valid_from.isoformat(),
            "valid_until": valid_until.isoformat(),
            "usage_limit": 100,
            "per_user_limit": 1,
        },
    )
    assert create_res.status_code == 201
    offer_data = create_res.json()["data"]
    assert offer_data["code"] == "WELCOME20"

    # 3. List active public offers
    list_res = await client.get("/api/v1/offers", headers=user_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()["data"]) >= 1

    # 4. Validate offer against a base amount of ₹1000 (100,000 minor)
    val_res = await client.post(
        "/api/v1/offers/validate",
        headers=user_headers,
        json={
            "code": "WELCOME20",
            "base_amount_minor": 100000,
        },
    )
    assert val_res.status_code == 200
    breakdown = val_res.json()["data"]
    assert breakdown["base_amount_minor"] == 100000
    assert breakdown["discount_amount_minor"] == 20000
    assert breakdown["payable_amount_minor"] == 80000
    assert breakdown["offer_applied"]["code"] == "WELCOME20"

    # 5. Validate with order amount below min threshold
    fail_res = await client.post(
        "/api/v1/offers/validate",
        headers=user_headers,
        json={
            "code": "WELCOME20",
            "base_amount_minor": 40000,  # ₹400 < ₹500 min
        },
    )
    assert fail_res.status_code == 400
    assert fail_res.json()["error"]["code"] == "OFFER_MINIMUM_ORDER_NOT_MET"
