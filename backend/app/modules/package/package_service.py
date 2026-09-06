"""Domain business logic for Packages and User Entitlement balances."""

import uuid
from datetime import UTC, datetime, timedelta

from pymongo.errors import DuplicateKeyError

from app.common.exceptions.app_exceptions import BadRequestException, NotFoundException
from app.common.exceptions.error_codes import ErrorCode
from app.common.utils.datetime_utils import utc_now
from app.modules.package.package_constants import PackageStatus
from app.modules.package.package_model import PackageProductInDB, UserPackageInDB
from app.modules.package.package_repository import PackageRepository
from app.modules.package.package_schema import (
    CreatePackageProductRequest,
    PackageProductResponse,
    UserPackageResponse,
)


class PackageService:
    """Service managing package catalog and user entitlement balance."""

    def __init__(self, package_repo: PackageRepository) -> None:
        self.package_repo = package_repo

    async def create_product(self, req: CreatePackageProductRequest) -> PackageProductResponse:
        """Create a new package template (Admin)."""
        now = utc_now()
        product = PackageProductInDB(
            id=str(uuid.uuid4()),
            title=req.title,
            description=req.description,
            session_count=req.session_count,
            validity_days=req.validity_days,
            price_minor=req.price_minor,
            currency=req.currency,
            is_active=req.is_active,
            created_at=now,
            updated_at=now,
        )
        saved = await self.package_repo.create_product(product)
        return PackageProductResponse.from_db(saved)

    async def list_active_products(self) -> list[PackageProductResponse]:
        """List packages available for purchase."""
        products = await self.package_repo.list_active_products()
        return [PackageProductResponse.from_db(p) for p in products]

    async def get_product(self, product_id: str) -> PackageProductResponse:
        product = await self.package_repo.get_product_by_id(product_id)
        if not product:
            raise NotFoundException(
                message=f"Package product '{product_id}' not found",
                code=ErrorCode.PACKAGE_NOT_FOUND,
            )
        return PackageProductResponse.from_db(product)

    async def fulfill_package_purchase(
        self, user_id: str, product_id: str, payment_id: str
    ) -> UserPackageInDB:
        """Called upon verified payment to grant user session entitlement. Idempotent per payment_id."""
        existing = await self.package_repo.get_user_package_by_payment_id(payment_id)
        if existing:
            return existing

        product = await self.package_repo.get_product_by_id(product_id)
        if not product:
            raise NotFoundException(
                message=f"Package product '{product_id}' not found",
                code=ErrorCode.PACKAGE_NOT_FOUND,
            )

        now = utc_now()
        expires_at = now + timedelta(days=product.validity_days)

        user_pkg = UserPackageInDB(
            id=str(uuid.uuid4()),
            user_id=user_id,
            package_product_id=product.id,
            title=product.title,
            total_sessions=product.session_count,
            remaining_sessions=product.session_count,
            purchased_at=now,
            expires_at=expires_at,
            payment_id=payment_id,
            status=PackageStatus.ACTIVE,
            created_at=now,
            updated_at=now,
        )
        try:
            return await self.package_repo.create_user_package(user_pkg)
        except DuplicateKeyError:
            pkg = await self.package_repo.get_user_package_by_payment_id(payment_id)
            if pkg:
                return pkg
            raise

    async def list_user_packages(self, user_id: str) -> list[UserPackageResponse]:
        """List all packages owned by a user."""
        pkgs = await self.package_repo.list_user_packages(user_id)
        return [UserPackageResponse.from_db(p) for p in pkgs]

    async def get_usable_packages(self, user_id: str) -> list[UserPackageResponse]:
        """Fetch unexpired packages with remaining sessions."""
        pkgs = await self.package_repo.get_active_usable_packages(user_id)
        return [UserPackageResponse.from_db(p) for p in pkgs]

    async def consume_session_for_booking(
        self, user_pkg_id: str, user_id: str, payment_id: str | None = None
    ) -> bool:
        """Atomically consume one session credit for consultation."""
        pkg = await self.package_repo.get_user_package_by_id(user_pkg_id)
        if not pkg or pkg.user_id != user_id:
            raise NotFoundException(
                message="Package not found or does not belong to you",
                code=ErrorCode.PACKAGE_NOT_FOUND,
            )

        now = datetime.now(UTC)
        if pkg.status != PackageStatus.ACTIVE or pkg.expires_at < now:
            raise BadRequestException(
                message="This package has expired or is inactive",
                code=ErrorCode.PACKAGE_EXPIRED,
            )

        # If this payment already consumed credit, return True
        if payment_id and payment_id in pkg.consumed_payment_ids:
            return True

        if pkg.remaining_sessions <= 0:
            raise BadRequestException(
                message="No remaining sessions available in this package",
                code=ErrorCode.PACKAGE_EXHAUSTED,
            )

        success = await self.package_repo.consume_session_atomic(
            user_pkg_id=user_pkg_id, user_id=user_id, payment_id=payment_id
        )
        if not success:
            raise BadRequestException(
                message="Unable to redeem package credit. No available sessions remaining.",
                code=ErrorCode.PACKAGE_EXHAUSTED,
            )
        return True
