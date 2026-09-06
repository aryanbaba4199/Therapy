"""Tests verifying review privacy boundaries, anonymous display name enforcement, and IDOR protection."""

from datetime import UTC, datetime
from typing import Any

import pytest
from httpx import AsyncClient

from app.modules.review.review_constants import ReviewStatus
from app.modules.review.review_model import ReviewInDB


@pytest.mark.asyncio
async def test_anonymous_review_enforces_safe_display_name(
    client: AsyncClient, mock_db: Any
) -> None:
    """An anonymous review must always serialize client_display_name as 'Anonymous Client'."""
    now = datetime.now(UTC)
    review = ReviewInDB(
        id="rev-anon-123",
        session_id="sess-anon-123",
        booking_id="bk-anon-123",
        therapist_id="th-anon-123",
        client_id="client-real-id",
        rating=5,
        comment="Great session.",
        client_display_name="Secret Real Name",  # Even if stored as something else
        is_anonymous=True,
        status=ReviewStatus.PUBLISHED,
        created_at=now,
        updated_at=now,
    )
    await mock_db["reviews"].insert_one(review.model_dump())

    # Public review list
    pub_res = await client.get("/api/v1/reviews/therapist/th-anon-123")
    assert pub_res.status_code == 200
    items = pub_res.json()["data"]
    assert len(items) == 1
    assert items[0]["client_display_name"] == "Anonymous Client"
    assert "client_id" not in items[0]


@pytest.mark.asyncio
async def test_review_detail_idor_protection(
    client: AsyncClient, mock_db: Any
) -> None:
    """An unrelated third-party client cannot inspect full internal review details."""
    now = datetime.now(UTC)
    review = ReviewInDB(
        id="rev-private-456",
        session_id="sess-private-456",
        booking_id="bk-private-456",
        therapist_id="th-private-456",
        client_id="client-owner-789",
        rating=4,
        comment="Helpful session.",
        client_display_name="Owner Name",
        is_anonymous=False,
        status=ReviewStatus.PUBLISHED,
        created_at=now,
        updated_at=now,
    )
    await mock_db["reviews"].insert_one(review.model_dump())

    # Register an unrelated user
    reg = await client.post(
        "/api/v1/auth/register",
        json={
            "first_name": "Unrelated",
            "last_name": "Stranger",
            "email": "stranger@example.com",
            "password": "Password123!",
        },
    )
    stranger_token = reg.json()["data"]["access_token"]
    stranger_headers = {"Authorization": f"Bearer {stranger_token}"}

    # Stranger calls detail endpoint -> 403 Forbidden
    res = await client.get(
        "/api/v1/reviews/rev-private-456",
        headers=stranger_headers,
    )
    assert res.status_code == 403
