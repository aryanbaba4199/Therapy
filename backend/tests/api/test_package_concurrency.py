"""Concurrency test for atomic package session consumption."""

import asyncio
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from mongomock_motor import AsyncMongoMockClient

from app.modules.package.package_constants import PackageStatus
from app.modules.package.package_model import UserPackageInDB
from app.modules.package.package_repository import PackageRepository


@pytest.mark.asyncio
async def test_atomic_package_concurrency() -> None:
    """Ensure that if a package only has 1 remaining session, concurrent requests atomically succeed once and fail subsequent ones."""
    mock_client: Any = AsyncMongoMockClient()
    mock_db = mock_client["oppam_therapy_test"]
    repo = PackageRepository(mock_db)

    # Seed a user package with exactly 1 remaining session
    now = datetime.now(UTC)
    user_package = UserPackageInDB(
        id=f"upkg_{uuid.uuid4().hex[:12]}",
        user_id="user_concurrent_123",
        package_product_id="prod_bundle_1",
        title="5 Sessions Bundle",
        total_sessions=5,
        remaining_sessions=1,
        status=PackageStatus.ACTIVE,
        expires_at=now + timedelta(days=30),
        payment_id="pay_init_123",
    )
    await repo.create_user_package(user_package)

    # Launch 5 concurrent session consumptions
    results = await asyncio.gather(
        *(repo.consume_session_atomic(user_package.id, user_package.user_id) for _ in range(5))
    )

    # Exactly 1 must return True, 4 must return False
    success_count = sum(1 for r in results if r is True)
    failure_count = sum(1 for r in results if r is False)

    assert success_count == 1
    assert failure_count == 4

    # The package should now have 0 remaining sessions and be EXHAUSTED
    updated = await repo.get_user_package_by_id(user_package.id)
    assert updated is not None
    assert updated.remaining_sessions == 0
    assert updated.status == PackageStatus.EXHAUSTED
