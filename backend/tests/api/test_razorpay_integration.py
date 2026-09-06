"""Comprehensive tests for Razorpay payment provider, HMAC verification, and webhooks."""

import hashlib
import hmac
import json
import uuid
from typing import Any

import pytest
from httpx import AsyncClient

from app.common.exceptions.error_codes import ErrorCode
from app.modules.payment.payment_constants import PaymentProviderName, PaymentStatus
from app.modules.payment.payment_provider import RazorpayPaymentProvider


def generate_hmac_sha256(secret: str, message: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()


@pytest.mark.asyncio
async def test_razorpay_provider_signature_verification() -> None:
    """Validate server-side signature calculation and comparison."""
    key_secret = "test_rzp_secret_key_12345"
    provider = RazorpayPaymentProvider(
        key_id="rzp_test_12345",
        key_secret=key_secret,
        webhook_secret="test_wh_secret_67890",
    )
    assert provider.name == PaymentProviderName.RAZORPAY

    order_id = "order_rzp_abc123"
    payment_id = "pay_rzp_xyz789"
    msg = f"{order_id}|{payment_id}".encode()
    valid_signature = generate_hmac_sha256(key_secret, msg)

    # Valid signature passes
    assert provider.verify_payment_signature(order_id, payment_id, valid_signature) is True

    # Tampered signature fails
    assert provider.verify_payment_signature(order_id, payment_id, "tampered_signature") is False

    # Tampered order ID fails
    assert provider.verify_payment_signature("order_other", payment_id, valid_signature) is False


@pytest.mark.asyncio
async def test_razorpay_provider_webhook_signature_verification() -> None:
    """Validate webhook signature verification against raw payload body bytes."""
    wh_secret = "wh_secret_razorpay_live_test"
    provider = RazorpayPaymentProvider(
        key_id="rzp_test_123",
        key_secret="rzp_secret_123",
        webhook_secret=wh_secret,
    )

    payload = json.dumps({"event": "payment.captured", "id": "evt_123"}).encode("utf-8")
    valid_header = generate_hmac_sha256(wh_secret, payload)

    assert provider.verify_webhook_signature(payload, valid_header, wh_secret) is True
    assert provider.verify_webhook_signature(payload, "invalid_sig", wh_secret) is False
    assert provider.verify_webhook_signature(payload + b"tampered", valid_header, wh_secret) is False


@pytest.mark.asyncio
async def test_payment_config_endpoint(client: AsyncClient) -> None:
    """Verify GET /payments/config exposes public payment configuration."""
    response = await client.get("/api/v1/payments/config")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "payment_provider" in data["data"]
    assert "razorpay_key_id" in data["data"]
    assert "razorpay_account_mode" in data["data"]


@pytest.mark.asyncio
async def test_razorpay_webhook_event_deduplication(
    client: AsyncClient, mock_db: Any
) -> None:
    """Verify that multiple deliveries of the exact same Razorpay webhook event ID are deduplicated."""
    event_id = f"evt_test_{uuid.uuid4().hex[:12]}"
    provider_order_id = f"order_{uuid.uuid4().hex[:12]}"
    provider_payment_id = f"pay_{uuid.uuid4().hex[:12]}"

    # Ensure indexes are created on mock_db
    from app.modules.payment.payment_repository import PaymentRepository
    payment_repo = PaymentRepository(mock_db)
    await payment_repo.ensure_indexes()

    # Seed an active payment
    payment_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    await mock_db["payments"].insert_one({
        "id": payment_id,
        "user_id": user_id,
        "target_type": "booking",
        "target_id": str(uuid.uuid4()),
        "amount_minor": 150000,
        "currency": "INR",
        "status": PaymentStatus.CREATED.value,
        "fulfillment_status": "pending",
        "provider": PaymentProviderName.MOCK.value,
        "provider_order_id": provider_order_id,
        "pricing": {
            "base_amount_minor": 150000,
            "discount_amount_minor": 0,
            "payable_amount_minor": 150000,
            "currency": "INR",
        },
        "created_at": "2026-09-06T10:00:00Z",
        "updated_at": "2026-09-06T10:00:00Z",
    })

    webhook_body = {
        "event": "payment.captured",
        "event_id": event_id,
        "provider_order_id": provider_order_id,
        "provider_payment_id": provider_payment_id,
        "amount_minor": 150000,
    }
    body_bytes = json.dumps(webhook_body).encode("utf-8")
    secret = "mock_webhook_secret_key_therapy_2026"
    sig = generate_hmac_sha256(secret, body_bytes)

    # First delivery
    res1 = await client.post(
        "/api/v1/payments/webhook",
        content=body_bytes,
        headers={"X-Payment-Signature": sig, "Content-Type": "application/json"},
    )
    assert res1.status_code == 200
    assert res1.json()["data"]["processed"] is True

    # Second delivery with exact same event ID -> should succeed idempotently
    res2 = await client.post(
        "/api/v1/payments/webhook",
        content=body_bytes,
        headers={"X-Payment-Signature": sig, "Content-Type": "application/json"},
    )
    assert res2.status_code == 200
    assert res2.json()["data"]["processed"] is True

    # Check database: exactly 1 webhook event record stored
    stored_events = await mock_db["payment_webhook_events"].count_documents({"event_id": event_id})
    assert stored_events == 1


@pytest.mark.asyncio
async def test_verify_payment_rejects_order_id_mismatch(
    client: AsyncClient, mock_db: Any
) -> None:
    """Verify that verify_payment fails if client submits an order ID different from the database record."""
    # Register client to obtain valid JWT token
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Test",
            "last_name": "Mismatch",
            "email": f"mismatch.{uuid.uuid4().hex[:8]}@oppam.in",
            "password": "Password123!",
        },
    )
    token = reg.json()["data"]["access_token"]
    user_id = reg.json()["data"]["user"]["id"]

    payment_id = str(uuid.uuid4())
    stored_order_id = "order_real_12345"
    await mock_db["payments"].insert_one({
        "id": payment_id,
        "user_id": user_id,
        "target_type": "booking",
        "target_id": str(uuid.uuid4()),
        "amount_minor": 100000,
        "currency": "INR",
        "status": "created",
        "fulfillment_status": "pending",
        "provider": "mock",
        "provider_order_id": stored_order_id,
        "pricing": {
            "base_amount_minor": 100000,
            "discount_amount_minor": 0,
            "payable_amount_minor": 100000,
            "currency": "INR",
        },
    })

    # Client submits different order_id
    res = await client.post(
        f"/api/v1/payments/{payment_id}/verify",
        json={
            "provider_order_id": "order_attacker_fake_999",
            "provider_payment_id": "pay_fake_123",
            "provider_signature": "signature_test",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 400
    assert res.json()["error"]["code"] == ErrorCode.PAYMENT_VERIFICATION_FAILED
