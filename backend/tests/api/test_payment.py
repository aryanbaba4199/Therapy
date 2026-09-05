"""Integration API tests for Payments, Webhooks, Package Redemption, and Booking Confirmation."""

from datetime import date, timedelta
from typing import Any

import pytest
from httpx import AsyncClient


async def _setup_reservation_for_payment(
    client: AsyncClient, mock_db: Any, client_token: str | None = None
) -> tuple[str, str, str]:
    """Sets up therapist, slot, client, and returns (reservation_id, client_token, therapist_id)."""
    th_reg = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Therapist",
            "last_name": "One",
            "email": f"th.pay.{date.today().isoformat()}@example.com",
            "password": "Password123!",
        },
    )
    th_token = th_reg.json()["data"]["access_token"]
    th_headers = {"Authorization": f"Bearer {th_token}"}

    th_res = await client.post(
        "/api/v1/therapists",
        headers=th_headers,
        json={
            "first_name": "Therapist",
            "last_name": "One",
            "display_name": "Dr. Therapist One",
            "bio": "Expert in anxiety and depression",
            "designation": "Psychologist",
            "specialization": "clinical_psychologist",
            "qualifications": ["M.Sc Psychology"],
            "experience_years": 8,
            "therapy_hours": 1500,
            "languages": ["ml", "en"],
            "expertises": ["anxiety"],
            "session_modes": ["online"],
            "pricing": {"amount": 1000, "currency": "INR", "duration_minutes": 60},
        },
    )
    therapist_id = th_res.json()["data"]["id"]
    await mock_db["therapists"].update_one(
        {"id": therapist_id},
        {"$set": {"status": "active", "verification.status": "verified"}},
    )

    day_str = (date.today() + timedelta(days=2)).isoformat()
    await client.post(
        f"/api/v1/therapists/{therapist_id}/extra-slots",
        headers=th_headers,
        json={
            "date": day_str,
            "start_time": "14:00",
            "end_time": "15:00",
            "session_mode": "online",
        },
    )
    slots_res = await client.get(
        f"/api/v1/therapists/{therapist_id}/slots?date={day_str}",
        headers=th_headers,
    )
    slot_id = slots_res.json()["data"][0]["id"]

    if not client_token:
        client_reg = await client.post(
            "/api/v1/auth/register",
            json={
                "first_name": "Pay",
                "last_name": "Client",
                "email": "pay.client@example.com",
                "password": "Password123!",
            },
        )
        client_token = client_reg.json()["data"]["access_token"]

    client_headers = {"Authorization": f"Bearer {client_token}"}

    res_hold = await client.post(
        "/api/v1/bookings/reservations",
        headers=client_headers,
        json={
            "therapist_id": therapist_id,
            "slot_id": slot_id,
            "slot_date": day_str,
            "session_mode": "online",
        },
    )
    reservation_id = res_hold.json()["data"]["id"]
    return reservation_id, client_token, therapist_id


@pytest.mark.asyncio
async def test_payment_initiation_and_mock_verification(client: AsyncClient, mock_db: Any) -> None:
    reservation_id, client_token, _ = await _setup_reservation_for_payment(client, mock_db)
    client_headers = {"Authorization": f"Bearer {client_token}"}

    # 1. Initiate payment with mock gateway
    init_res = await client.post(
        "/api/v1/payments",
        headers=client_headers,
        json={
            "target_type": "booking",
            "target_id": reservation_id,
            "payment_method": "upi",
            "idempotency_key": f"idem-{reservation_id}",
        },
    )
    assert init_res.status_code == 201
    pay_data = init_res.json()["data"]
    payment_id = pay_data["id"]
    provider_order_id = pay_data["provider_order_id"]
    assert pay_data["status"] == "created"
    assert pay_data["amount_minor"] == 100000  # ₹1000

    # 2. Verify payment with valid mock signature
    from app.core.config import get_settings
    from app.modules.payment.payment_provider import MockPaymentProvider

    provider = MockPaymentProvider(get_settings().payment_webhook_secret)
    valid_sig = provider.generate_signature(provider_order_id, "pay_mock_123")

    verify_res = await client.post(
        f"/api/v1/payments/{payment_id}/verify",
        headers=client_headers,
        json={
            "provider_order_id": provider_order_id,
            "provider_payment_id": "pay_mock_123",
            "provider_signature": valid_sig,
        },
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["data"]["status"] == "paid"

    # 3. Check that booking is now confirmed in bookings collection
    confirmed_booking = await mock_db["bookings"].find_one({"reservation_id": reservation_id})
    assert confirmed_booking is not None
    assert confirmed_booking["status"] == "confirmed"


@pytest.mark.asyncio
async def test_package_purchase_and_redemption(client: AsyncClient, mock_db: Any) -> None:
    # 1. Create admin and package product
    admin_reg = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Admin",
            "last_name": "PkgPay",
            "email": "admin.pkgpay@example.com",
            "password": "Password123!",
        },
    )
    admin_id = admin_reg.json()["data"]["user"]["id"]
    admin_token = admin_reg.json()["data"]["access_token"]
    await mock_db["users"].update_one({"id": admin_id}, {"$set": {"roles": ["admin"]}})
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    prod_res = await client.post(
        "/api/v1/packages",
        headers=admin_headers,
        json={
            "title": "3 Sessions Wellness Pack",
            "description": "Save on 3 sessions",
            "session_count": 3,
            "validity_days": 60,
            "price_minor": 270000,
        },
    )
    assert prod_res.status_code == 201
    prod_id = prod_res.json()["data"]["id"]

    # 2. Client purchases package
    client_reg = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "PkgBuyer",
            "last_name": "Client",
            "email": "buyer.client@example.com",
            "password": "Password123!",
        },
    )
    client_token = client_reg.json()["data"]["access_token"]
    client_headers = {"Authorization": f"Bearer {client_token}"}

    pay_init = await client.post(
        "/api/v1/payments",
        headers=client_headers,
        json={
            "target_type": "package",
            "target_id": prod_id,
            "payment_method": "card",
        },
    )
    assert pay_init.status_code == 201
    payment_id = pay_init.json()["data"]["id"]
    order_id = pay_init.json()["data"]["provider_order_id"]

    from app.core.config import get_settings
    from app.modules.payment.payment_provider import MockPaymentProvider

    provider = MockPaymentProvider(get_settings().payment_webhook_secret)
    sig = provider.generate_signature(order_id, "pay_mock_123")

    verify_res = await client.post(
        f"/api/v1/payments/{payment_id}/verify",
        headers=client_headers,
        json={
            "provider_order_id": order_id,
            "provider_payment_id": "pay_mock_123",
            "provider_signature": sig,
        },
    )
    assert verify_res.status_code == 200

    # Verify user now has 1 user_package with 3 remaining sessions
    my_pkgs = await client.get("/api/v1/packages/my", headers=client_headers)
    assert my_pkgs.status_code == 200
    assert len(my_pkgs.json()["data"]) == 1
    user_pkg = my_pkgs.json()["data"][0]
    user_pkg_id = user_pkg["id"]
    assert user_pkg["remaining_sessions"] == 3
    assert user_pkg["status"] == "active"

    # 3. Now let's redeem 1 session from this package for a new booking using the SAME client!
    reservation_id, _, _ = await _setup_reservation_for_payment(client, mock_db, client_token=client_token)
    # Redeem using package credit
    redeem_pay = await client.post(
        "/api/v1/payments",
        headers=client_headers,
        json={
            "target_type": "booking",
            "target_id": reservation_id,
            "payment_method": "package_redemption",
            "user_package_id": user_pkg_id,
        },
    )
    assert redeem_pay.status_code == 201
    redeem_data = redeem_pay.json()["data"]
    # Should be immediately paid with 0 amount payable!
    assert redeem_data["status"] == "paid"
    assert redeem_data["amount_minor"] == 0
    assert redeem_data["payment_method"] == "package_redemption"

    # Booking should be confirmed immediately
    confirmed = await mock_db["bookings"].find_one({"reservation_id": reservation_id})
    assert confirmed is not None
    assert confirmed["status"] == "confirmed"

    # And remaining sessions on user package should now be 2!
    my_pkgs_after = await client.get("/api/v1/packages/my", headers=client_headers)
    assert my_pkgs_after.json()["data"][0]["remaining_sessions"] == 2
