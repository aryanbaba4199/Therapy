"""Tests verifying commercial package fulfillment idempotency and fulfillment status tracking."""

from typing import Any

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_repeated_package_fulfillment_is_idempotent(
    client: AsyncClient, mock_db: Any
) -> None:
    """Repeated calls to fulfill package purchase with the same payment_id returns existing entitlement without creating duplicate packages."""
    # Register user
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Manju",
            "last_name": "Warrier",
            "email": "manju@example.com",
            "password": "Password123!",
        },
    )
    user_token = reg.json()["data"]["access_token"]
    reg.json()["data"]["user"]["id"]
    headers = {"Authorization": f"Bearer {user_token}"}

    # Seed package product
    from app.modules.package.package_model import PackageProductInDB

    package_product = PackageProductInDB(
        id="pkg-prod-wellness-1",
        title="Mindful Journey (3 Sessions)",
        description="Save on 3 sessions",
        session_count=3,
        validity_days=60,
        price_minor=300000,
        currency="INR",
        is_active=True,
    )
    await mock_db["package_products"].insert_one(package_product.model_dump())

    # Fetch available packages
    pkg_list = await client.get("/api/v1/packages")
    assert pkg_list.status_code == 200
    packages = pkg_list.json()["data"]
    package_id = packages[0]["id"]

    # Initiate purchase
    pay_init = await client.post(
        "/api/v1/payments",
        headers=headers,
        json={"target_type": "package", "target_id": package_id},
    )
    assert pay_init.status_code == 201
    payment_data = pay_init.json()["data"]
    payment_id = payment_data["id"]
    order_id = payment_data["provider_order_id"]

    from app.core.config import get_settings
    from app.modules.payment.payment_provider import MockPaymentProvider

    provider = MockPaymentProvider(get_settings().payment_webhook_secret)
    valid_sig = provider.generate_signature(order_id, "pay_test_123")

    # Verify payment (1st time)
    verify_1 = await client.post(
        f"/api/v1/payments/{payment_id}/verify",
        headers=headers,
        json={
            "provider_order_id": order_id,
            "provider_payment_id": "pay_test_123",
            "provider_signature": valid_sig,
            "payment_method": "upi",
        },
    )
    assert verify_1.status_code == 200
    assert verify_1.json()["data"]["status"] == "paid"
    assert verify_1.json()["data"]["fulfillment_status"] == "fulfilled"

    # Count packages owned by user
    user_pkgs_1 = await client.get("/api/v1/packages/my", headers=headers)
    assert len(user_pkgs_1.json()["data"]) == 1

    # Verify payment (2nd time - idempotency retry)
    verify_2 = await client.post(
        f"/api/v1/payments/{payment_id}/verify",
        headers=headers,
        json={
            "provider_order_id": order_id,
            "provider_payment_id": "pay_test_123",
            "provider_signature": valid_sig,
        },
    )
    assert verify_2.status_code == 200
    assert verify_2.json()["data"]["status"] == "paid"
    assert verify_2.json()["data"]["fulfillment_status"] == "fulfilled"

    # Invariant: User still has exactly 1 package entitlement, NOT 2
    user_pkgs_2 = await client.get("/api/v1/packages/my", headers=headers)
    assert len(user_pkgs_2.json()["data"]) == 1
