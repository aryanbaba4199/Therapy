"""Presentation controller for Package endpoints."""

from app.common.responses.api_response import ApiResponse, success_response
from app.modules.package.package_schema import (
    CreatePackageProductRequest,
    PackageProductResponse,
    UserPackageResponse,
)
from app.modules.package.package_service import PackageService
from app.modules.user.user_model import UserInDB


class PackageController:
    """Controller handling package product catalog and user balance endpoints."""

    def __init__(self, service: PackageService) -> None:
        self.service = service

    async def create_product(
        self, req: CreatePackageProductRequest
    ) -> ApiResponse[PackageProductResponse]:
        res = await self.service.create_product(req)
        return success_response(data=res, message="Package product created successfully")

    async def list_products(self) -> ApiResponse[list[PackageProductResponse]]:
        res = await self.service.list_active_products()
        return success_response(data=res)

    async def get_product(self, product_id: str) -> ApiResponse[PackageProductResponse]:
        res = await self.service.get_product(product_id)
        return success_response(data=res)

    async def list_my_packages(self, caller: UserInDB) -> ApiResponse[list[UserPackageResponse]]:
        res = await self.service.list_user_packages(caller.id)
        return success_response(data=res)

    async def list_my_usable_packages(
        self, caller: UserInDB
    ) -> ApiResponse[list[UserPackageResponse]]:
        res = await self.service.get_usable_packages(caller.id)
        return success_response(data=res)

