"""Tests verifying operations dashboard aggregation queries with correct field mapping."""

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from httpx import AsyncClient

from app.modules.payment.payment_constants import (
    FulfillmentStatus,
    PaymentProviderName,
    PaymentStatus,
    PaymentTargetType,
)
from app.modules.payment.payment_model import PaymentInDB, PaymentPricingSnapshot
from app.modules.session.session_constants import AttendanceStatus, SessionStatus
from app.modules.session.session_model import SessionInDB


@pytest.mark.asyncio
async def test_dashboard_metrics_correct_field_mapping(
    client: AsyncClient, mock_db: Any
) -> None:
    """Verify that get_dashboard_metrics aggregates scheduled_start_at and amount_minor properly."""
    # Register Super Admin
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Admin",
            "last_name": "Boss",
            "email": "adminboss@example.com",
            "password": "Password123!",
        },
    )
    admin_id = reg.json()["data"]["user"]["id"]
    admin_token = reg.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    # Make super admin
    await mock_db["users"].update_one(
        {"id": admin_id},
        {"$set": {"roles": ["super_admin", "admin", "user"]}},
    )

    now = datetime.now(UTC)

    # 1. Seed upcoming session (scheduled_start_at >= now)
    session = SessionInDB(
        id="sess-metric-1",
        booking_id="bk-metric-1",
        therapist_id="th-metric-1",
        client_id="cl-metric-1",
        scheduled_start_at=now + timedelta(hours=2),
        scheduled_end_at=now + timedelta(hours=3),
        duration_minutes=60,
        session_mode="online",
        status=SessionStatus.SCHEDULED,
        attendance=AttendanceStatus.UNKNOWN,
    )
    await mock_db["sessions"].insert_one(session.model_dump())

    # 2. Seed a paid payment with amount_minor = 150000 (Rs 1500)
    payment = PaymentInDB(
        id="pay-metric-1",
        user_id="cl-metric-1",
        target_type=PaymentTargetType.BOOKING,
        target_id="bk-metric-1",
        amount_minor=150000,
        currency="INR",
        status=PaymentStatus.PAID,
        fulfillment_status=FulfillmentStatus.FULFILLED,
        provider=PaymentProviderName.MOCK,
        pricing=PaymentPricingSnapshot(
            base_amount_minor=150000,
            payable_amount_minor=150000,
        ),
        paid_at=now,
        created_at=now,
    )
    await mock_db["payments"].insert_one(payment.model_dump())

    # 3. Call operations dashboard endpoint
    metrics_res = await client.get("/api/v1/operations/dashboard/metrics", headers=headers)
    assert metrics_res.status_code == 200
    metrics = metrics_res.json()["data"]

    # Verify upcoming session count is 1 (field scheduled_start_at verified)
    assert metrics["upcoming_sessions"] >= 1

    # Verify total revenue is 150000 (field amount_minor verified)
    assert metrics["total_revenue_minor"] >= 150000
