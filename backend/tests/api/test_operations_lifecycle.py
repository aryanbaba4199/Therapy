"""Integration tests for Operations, Admin dashboard, user management, leads, and audit logging."""

import uuid
from typing import Any
import pytest
from httpx import AsyncClient

from app.modules.operations.operations_constants import AuditAction, LeadSource, LeadStatus
from app.modules.user.user_constants import UserRole, UserStatus


async def create_user_with_roles(
    client: AsyncClient, mock_db: Any, first_name: str, roles: list[str]
) -> tuple[dict[str, str], str]:
    """Helper to register user and update roles."""
    email = f"{first_name.lower()}.{uuid.uuid4().hex[:6]}@example.com"
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": first_name,
            "last_name": "Test",
            "email": email,
            "password": "Password123!",
        },
    )
    user_id = reg.json()["data"]["user"]["id"]
    token = reg.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    if roles != ["user"]:
        await mock_db["users"].update_one(
            {"id": user_id}, {"$set": {"roles": roles}}
        )
    return headers, user_id


@pytest.mark.asyncio
async def test_admin_dashboard_and_permissions(
    client: AsyncClient,
    mock_db: Any,
) -> None:
    """Verify dashboard metrics visibility and permission enforcement."""
    admin_headers, _ = await create_user_with_roles(
        client, mock_db, "Admin", [UserRole.ADMIN.value]
    )
    user_headers, _ = await create_user_with_roles(
        client, mock_db, "Client", [UserRole.USER.value]
    )

    # Regular client should be rejected with 403 Forbidden
    res_client = await client.get("/api/v1/operations/dashboard/metrics", headers=user_headers)
    assert res_client.status_code == 403

    # Admin should receive aggregated metrics envelope
    res_admin = await client.get("/api/v1/operations/dashboard/metrics", headers=admin_headers)
    assert res_admin.status_code == 200
    data = res_admin.json()["data"]
    assert "today_bookings" in data
    assert "upcoming_sessions" in data
    assert "active_therapists" in data
    assert "pending_support_tickets" in data
    assert "total_revenue_minor" in data
    assert "new_leads_count" in data


@pytest.mark.asyncio
async def test_user_management_and_audit_logging(
    client: AsyncClient,
    mock_db: Any,
) -> None:
    """Verify user suspension, role management protection, and audit logs."""
    super_admin_headers, _ = await create_user_with_roles(
        client, mock_db, "SuperAdmin", [UserRole.SUPER_ADMIN.value]
    )
    admin_headers, _ = await create_user_with_roles(
        client, mock_db, "AdminTwo", [UserRole.ADMIN.value]
    )
    target_headers, target_user_id = await create_user_with_roles(
        client, mock_db, "TargetClient", [UserRole.USER.value]
    )

    # 1. Admin suspends a target client
    suspend_res = await client.patch(
        f"/api/v1/operations/users/{target_user_id}/status",
        headers=admin_headers,
        json={"status": UserStatus.SUSPENDED.value, "reason": "Violation of terms of service"},
    )
    assert suspend_res.status_code == 200
    assert suspend_res.json()["data"]["status"] == UserStatus.SUSPENDED.value

    # Suspended client is now blocked from active routes
    blocked_res = await client.get("/api/v1/users/me", headers=target_headers)
    assert blocked_res.status_code == 403

    # 2. Ordinary Admin cannot elevate user to Admin or Super Admin
    role_escalate_res = await client.patch(
        f"/api/v1/operations/users/{target_user_id}/roles",
        headers=admin_headers,
        json={"roles": [UserRole.ADMIN.value], "reason": "Attempted elevation"},
    )
    assert role_escalate_res.status_code == 403

    # 3. Super Admin can update roles
    super_role_res = await client.patch(
        f"/api/v1/operations/users/{target_user_id}/roles",
        headers=super_admin_headers,
        json={"roles": [UserRole.STAFF.value], "reason": "Hired as support staff"},
    )
    assert super_role_res.status_code == 200
    assert UserRole.STAFF.value in super_role_res.json()["data"]["roles"]

    # 4. Verify audit trail records were generated
    audit_res = await client.get(
        f"/api/v1/operations/audit-logs?resource_id={target_user_id}", headers=admin_headers
    )
    assert audit_res.status_code == 200
    audit_items = audit_res.json()["data"]
    assert len(audit_items) >= 2
    actions = [a["action"] for a in audit_items]
    assert AuditAction.USER_STATUS_UPDATED.value in actions
    assert AuditAction.USER_ROLES_UPDATED.value in actions


@pytest.mark.asyncio
async def test_lead_lifecycle_and_assignment(
    client: AsyncClient,
    mock_db: Any,
) -> None:
    """Verify first responder lead creation, assignment, status update, and conversion."""
    fr_headers, _ = await create_user_with_roles(
        client, mock_db, "FirstRespOne", [UserRole.FIRST_RESPONDER.value]
    )
    fr2_headers, fr2_user_id = await create_user_with_roles(
        client, mock_db, "FirstRespTwo", [UserRole.FIRST_RESPONDER.value]
    )
    client_headers, client_user_id = await create_user_with_roles(
        client, mock_db, "ClientConv", [UserRole.USER.value]
    )

    # 1. Create prospective lead
    create_res = await client.post(
        "/api/v1/operations/leads",
        headers=fr_headers,
        json={
            "name": "Jane Doe",
            "phone": "+919876543210",
            "email": "jane.doe@example.com",
            "source": LeadSource.HELPLINE.value,
            "notes": "Inquired about depression counseling",
        },
    )
    assert create_res.status_code == 200
    lead_id = create_res.json()["data"]["id"]
    assert create_res.json()["data"]["status"] == LeadStatus.NEW.value

    # 2. Update lead status to contacted
    update_res = await client.patch(
        f"/api/v1/operations/leads/{lead_id}",
        headers=fr_headers,
        json={"status": LeadStatus.CONTACTED.value, "notes": "Left voicemail, requested callback"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["data"]["status"] == LeadStatus.CONTACTED.value
    assert update_res.json()["data"]["last_contacted_at"] is not None

    # 3. Reassign lead to another first responder
    assign_res = await client.post(
        f"/api/v1/operations/leads/{lead_id}/assign",
        headers=fr_headers,
        json={"assigned_to": fr2_user_id, "notes": "Handing off due to shift end"},
    )
    assert assign_res.status_code == 200
    assert assign_res.json()["data"]["assigned_to"] == fr2_user_id

    # 4. Convert lead to registered user
    convert_res = await client.post(
        f"/api/v1/operations/leads/{lead_id}/convert/{client_user_id}",
        headers=fr2_headers,
    )
    assert convert_res.status_code == 200
    assert convert_res.json()["data"]["status"] == LeadStatus.CONVERTED.value
    assert convert_res.json()["data"]["converted_user_id"] == client_user_id

    # 5. Regular client cannot access leads
    unauth_lead_res = await client.get("/api/v1/operations/leads", headers=client_headers)
    assert unauth_lead_res.status_code == 403
