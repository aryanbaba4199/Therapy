"""Security and IDOR authorization test suite for Support domain."""

import uuid
from typing import Any

import pytest
from httpx import AsyncClient

from app.modules.support.support_constants import SupportCategory


@pytest.mark.asyncio
async def test_support_reference_idor_and_ticket_isolation(
    client: AsyncClient, mock_db: Any
) -> None:
    """Validate cross-user IDOR protections: users cannot reference other users' bookings/payments/sessions or access other users' tickets."""
    # 1. Register Client A
    reg_a = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Alice",
            "last_name": "Smith",
            "email": f"alice.{uuid.uuid4().hex[:6]}@example.com",
            "password": "Password123!",
        },
    )
    cl_a_token = reg_a.json()["data"]["access_token"]
    cl_a_headers = {"Authorization": f"Bearer {cl_a_token}"}

    # 2. Register Client B
    reg_b = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Bob",
            "last_name": "Jones",
            "email": f"bob.{uuid.uuid4().hex[:6]}@example.com",
            "password": "Password123!",
        },
    )
    cl_b_id = reg_b.json()["data"]["user"]["id"]
    cl_b_token = reg_b.json()["data"]["access_token"]
    cl_b_headers = {"Authorization": f"Bearer {cl_b_token}"}

    # 3. Create mock booking, payment, and package owned by Client B
    fake_booking_b_id = str(uuid.uuid4())
    await mock_db["bookings"].insert_one(
        {"id": fake_booking_b_id, "client_id": cl_b_id, "status": "confirmed"}
    )

    fake_payment_b_id = str(uuid.uuid4())
    await mock_db["payments"].insert_one(
        {"id": fake_payment_b_id, "user_id": cl_b_id, "status": "paid"}
    )

    fake_package_b_id = str(uuid.uuid4())
    await mock_db["user_packages"].insert_one(
        {"id": fake_package_b_id, "user_id": cl_b_id, "status": "active"}
    )

    fake_session_b_id = str(uuid.uuid4())
    await mock_db["sessions"].insert_one(
        {"id": fake_session_b_id, "client_id": cl_b_id, "therapist_id": "th-123", "status": "completed"}
    )

    # 4. Client A attempts to create ticket referencing Client B's booking -> 403 FORBIDDEN
    res_bkg_idor = await client.post(
        "/api/v1/support/tickets",
        headers=cl_a_headers,
        json={
            "category": SupportCategory.BOOKING.value,
            "subject": "Issues with my booking",
            "description": "Please help me cancel this booking.",
            "booking_id": fake_booking_b_id,
        },
    )
    assert res_bkg_idor.status_code == 403
    assert res_bkg_idor.json()["error"]["code"] == "SUPPORT_TICKET_REFERENCE_FORBIDDEN"

    # 5. Client A attempts to create ticket referencing Client B's payment -> 403 FORBIDDEN
    res_pay_idor = await client.post(
        "/api/v1/support/tickets",
        headers=cl_a_headers,
        json={
            "category": SupportCategory.PAYMENT.value,
            "subject": "Payment refund request",
            "description": "I need a refund for this payment.",
            "payment_id": fake_payment_b_id,
        },
    )
    assert res_pay_idor.status_code == 403
    assert res_pay_idor.json()["error"]["code"] == "SUPPORT_TICKET_REFERENCE_FORBIDDEN"

    # 6. Client A attempts to create ticket referencing Client B's package -> 403 FORBIDDEN
    res_pkg_idor = await client.post(
        "/api/v1/support/tickets",
        headers=cl_a_headers,
        json={
            "category": SupportCategory.PACKAGE.value,
            "subject": "Package balance incorrect",
            "description": "My session credits are missing.",
            "package_id": fake_package_b_id,
        },
    )
    assert res_pkg_idor.status_code == 403
    assert res_pkg_idor.json()["error"]["code"] == "SUPPORT_TICKET_REFERENCE_FORBIDDEN"

    # 7. Client A attempts to create ticket referencing Client B's session -> 403 FORBIDDEN
    res_sess_idor = await client.post(
        "/api/v1/support/tickets",
        headers=cl_a_headers,
        json={
            "category": SupportCategory.SESSION.value,
            "subject": "Session connection failure",
            "description": "Session failed to connect.",
            "session_id": fake_session_b_id,
        },
    )
    assert res_sess_idor.status_code == 403
    assert res_sess_idor.json()["error"]["code"] == "SUPPORT_TICKET_REFERENCE_FORBIDDEN"

    # 8. Client B creates a legitimate ticket
    res_ticket_b = await client.post(
        "/api/v1/support/tickets",
        headers=cl_b_headers,
        json={
            "category": SupportCategory.BOOKING.value,
            "subject": "Bob's legitimate inquiry",
            "description": "This is Bob asking about my own booking.",
            "booking_id": fake_booking_b_id,
        },
    )
    assert res_ticket_b.status_code == 201
    ticket_b_id = res_ticket_b.json()["data"]["id"]

    # 9. Client A attempts to GET Client B's ticket -> 403 FORBIDDEN
    res_get_idor = await client.get(
        f"/api/v1/support/tickets/{ticket_b_id}", headers=cl_a_headers
    )
    assert res_get_idor.status_code == 403
    assert res_get_idor.json()["error"]["code"] == "SUPPORT_TICKET_FORBIDDEN"

    # 10. Client A attempts to message Client B's ticket -> 403 FORBIDDEN
    res_msg_idor = await client.post(
        f"/api/v1/support/tickets/{ticket_b_id}/messages",
        headers=cl_a_headers,
        json={"message": "Injected unauthorized message by Alice"},
    )
    assert res_msg_idor.status_code == 403
    assert res_msg_idor.json()["error"]["code"] == "SUPPORT_MESSAGE_FORBIDDEN"

    # 11. Client A attempts to close Client B's ticket -> 403 FORBIDDEN
    res_close_idor = await client.post(
        f"/api/v1/support/tickets/{ticket_b_id}/close", headers=cl_a_headers
    )
    assert res_close_idor.status_code == 403
    assert res_close_idor.json()["error"]["code"] == "SUPPORT_TICKET_FORBIDDEN"

    # 12. Non-staff Client A attempts staff endpoint -> 403 FORBIDDEN
    res_staff_ep = await client.get(
        "/api/v1/support/staff/tickets", headers=cl_a_headers
    )
    assert res_staff_ep.status_code == 403
