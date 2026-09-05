"""Integration tests for Support ticket lifecycle, conversation thread, and staff workflows."""

import uuid
from typing import Any

import pytest
from httpx import AsyncClient

from app.modules.support.support_constants import (
    SupportCategory,
    SupportPriority,
    SupportTicketStatus,
)


@pytest.mark.asyncio
async def test_support_ticket_lifecycle_and_conversations(
    client: AsyncClient, mock_db: Any
) -> None:
    """Test ticket creation, conversation replies, staff assignments, status progression, and closing."""
    # 1. Register Client user
    cl_email = f"client.{uuid.uuid4().hex[:6]}@example.com"
    cl_reg = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Meera",
            "last_name": "Nair",
            "email": cl_email,
            "password": "Password123!",
        },
    )
    cl_token = cl_reg.json()["data"]["access_token"]
    cl_headers = {"Authorization": f"Bearer {cl_token}"}

    # 2. Register Staff user
    staff_email = f"staff.{uuid.uuid4().hex[:6]}@example.com"
    st_reg = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Rahul",
            "last_name": "Support",
            "email": staff_email,
            "password": "Password123!",
        },
    )
    staff_user_id = st_reg.json()["data"]["user"]["id"]
    staff_token = st_reg.json()["data"]["access_token"]
    staff_headers = {"Authorization": f"Bearer {staff_token}"}
    await mock_db["users"].update_one(
        {"id": staff_user_id}, {"$set": {"roles": ["staff"]}}
    )

    # 3. Client creates a support ticket
    res_create = await client.post(
        "/api/v1/support/tickets",
        headers=cl_headers,
        json={
            "category": SupportCategory.TECHNICAL.value,
            "subject": "Audio glitch during consultation",
            "description": "I could not hear the therapist clearly during the first 5 minutes.",
            "priority": SupportPriority.NORMAL.value,
        },
    )
    assert res_create.status_code == 201
    ticket_data = res_create.json()["data"]
    ticket_id = ticket_data["id"]
    assert ticket_data["status"] == SupportTicketStatus.OPEN.value
    assert ticket_data["category"] == SupportCategory.TECHNICAL.value
    assert "TCK-" in ticket_data["ticket_number"]

    # 4. Client lists their tickets
    res_list = await client.get("/api/v1/support/tickets", headers=cl_headers)
    assert res_list.status_code == 200
    my_tickets = res_list.json()["data"]
    assert len(my_tickets) >= 1
    assert any(t["id"] == ticket_id for t in my_tickets)

    # 5. Client retrieves ticket detail with conversation
    res_detail = await client.get(
        f"/api/v1/support/tickets/{ticket_id}", headers=cl_headers
    )
    assert res_detail.status_code == 200
    detail_data = res_detail.json()["data"]
    assert detail_data["ticket"]["id"] == ticket_id
    # Opening message was auto-created from description
    messages = detail_data["messages"]
    assert len(messages) == 1
    assert "Audio glitch" in messages[0]["message"] or "could not hear" in messages[0]["message"]

    # 6. Staff lists all tickets across the platform
    res_staff_list = await client.get(
        "/api/v1/support/staff/tickets", headers=staff_headers
    )
    assert res_staff_list.status_code == 200
    staff_items = res_staff_list.json()["data"]
    assert any(t["id"] == ticket_id for t in staff_items)

    # 7. Staff assigns ticket to himself
    res_assign = await client.post(
        f"/api/v1/support/staff/tickets/{ticket_id}/assign",
        headers=staff_headers,
        json={"staff_id": staff_user_id},
    )
    assert res_assign.status_code == 200
    assigned_ticket = res_assign.json()["data"]
    assert assigned_ticket["assigned_to"] == staff_user_id
    assert assigned_ticket["status"] == SupportTicketStatus.IN_PROGRESS.value

    # 8. Staff posts a reply to client
    res_staff_msg = await client.post(
        f"/api/v1/support/tickets/{ticket_id}/messages",
        headers=staff_headers,
        json={
            "message": "Hello Meera, we are looking into the audio logs for your session.",
            "is_internal_note": False,
        },
    )
    assert res_staff_msg.status_code == 201

    # 9. Staff posts an internal note
    res_internal_msg = await client.post(
        f"/api/v1/support/tickets/{ticket_id}/messages",
        headers=staff_headers,
        json={
            "message": "INTERNAL: Checked WebRTC server latency, was normal. Probably client mic issue.",
            "is_internal_note": True,
        },
    )
    assert res_internal_msg.status_code == 201

    # 10. Client views ticket: internal note MUST NOT be visible!
    res_cl_view = await client.get(
        f"/api/v1/support/tickets/{ticket_id}", headers=cl_headers
    )
    assert res_cl_view.status_code == 200
    cl_msgs = res_cl_view.json()["data"]["messages"]
    # Should only see 2 messages (opening + staff reply), NOT the internal note
    assert len(cl_msgs) == 2
    for m in cl_msgs:
        assert "INTERNAL:" not in m["message"]
        assert m["is_internal_note"] is False

    # 11. Staff views ticket: internal note IS visible
    res_st_view = await client.get(
        f"/api/v1/support/tickets/{ticket_id}", headers=staff_headers
    )
    assert res_st_view.status_code == 200
    st_msgs = res_st_view.json()["data"]["messages"]
    assert len(st_msgs) == 3

    # 12. Client replies back
    res_cl_reply = await client.post(
        f"/api/v1/support/tickets/{ticket_id}/messages",
        headers=cl_headers,
        json={"message": "Thank you, it resolved after I reconnected."},
    )
    assert res_cl_reply.status_code == 201

    # 13. Client closes ticket
    res_close = await client.post(
        f"/api/v1/support/tickets/{ticket_id}/close", headers=cl_headers
    )
    assert res_close.status_code == 200
    assert res_close.json()["data"]["status"] == SupportTicketStatus.CLOSED.value

    # 14. Client attempts to message closed ticket -> rejected with 400
    res_closed_msg = await client.post(
        f"/api/v1/support/tickets/{ticket_id}/messages",
        headers=cl_headers,
        json={"message": "Can I still ask a question?"},
    )
    assert res_closed_msg.status_code == 400
    assert res_closed_msg.json()["error"]["code"] == "SUPPORT_TICKET_INVALID_STATE"
