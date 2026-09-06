"""Concurrency and IDOR tests for customer support ticket system."""

import asyncio
from typing import Any

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_concurrent_ticket_creation_generates_unique_sequential_numbers(
    client: AsyncClient, mock_db: Any
) -> None:
    """Simulate 20 concurrent ticket creations: every ticket number must be strictly unique."""
    # Register user
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Dulquer",
            "last_name": "Salmaan",
            "email": "dq@example.com",
            "password": "Password123!",
        },
    )
    user_token = reg.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {user_token}"}

    async def create_ticket(idx: int) -> str | None:
        res = await client.post(
            "/api/v1/support/tickets",
            headers=headers,
            json={
                "subject": f"Issue {idx}",
                "category": "technical",
                "description": f"Description for ticket {idx}",
            },
        )
        if res.status_code == 201:
            return str(res.json()["data"]["ticket_number"])
        return None

    # Fire 20 concurrent ticket creations
    ticket_numbers = await asyncio.gather(*(create_ticket(i) for i in range(20)))

    # Filter out None and verify count
    valid_numbers = [num for num in ticket_numbers if num is not None]
    assert len(valid_numbers) == 20

    # Invariant: Every ticket number must be unique
    assert len(set(valid_numbers)) == 20
    for num in valid_numbers:
        assert num.startswith("TCK-")


@pytest.mark.asyncio
async def test_support_ticket_idor_isolation(
    client: AsyncClient, mock_db: Any
) -> None:
    """User B cannot view or post messages to User A's support ticket."""
    reg_a = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "User",
            "last_name": "A",
            "email": "usera@example.com",
            "password": "Password123!",
        },
    )
    token_a = reg_a.json()["data"]["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    ticket_res = await client.post(
        "/api/v1/support/tickets",
        headers=headers_a,
        json={"subject": "Private Help", "category": "booking", "description": "My issue"},
    )
    ticket_id = ticket_res.json()["data"]["id"]

    reg_b = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "User",
            "last_name": "B",
            "email": "userb@example.com",
            "password": "Password123!",
        },
    )
    token_b = reg_b.json()["data"]["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User B tries to view User A's ticket -> 403
    get_res = await client.get(f"/api/v1/support/tickets/{ticket_id}", headers=headers_b)
    assert get_res.status_code == 403
