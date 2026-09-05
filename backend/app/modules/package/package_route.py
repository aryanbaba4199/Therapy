"""API endpoints for Package products and User entitlements."""

from fastapi import APIRouter, Depends

from app.common.responses.api_response import ApiResponse
from app.modules.auth.auth_dependency import get_current_active_user, require_roles
from app.modules.package.package_controller import PackageController
from app.modules.package.package_dependency import get_package_service
from app.modules.package.package_schema import (
    CreatePackageProductRequest,
    PackageProductResponse,
    UserPackageResponse,
)
from app.modules.package.package_service import PackageService
from app.modules.user.user_constants import UserRole
from app.modules.user.user_model import UserInDB

router = APIRouter(prefix="/packages", tags=["Packages & Sessions"])


def get_package_controller(
    service: PackageService = Depends(get_package_service),
) -> PackageController:
    return PackageController(service=service)


@router.get(
    "",
    response_model=ApiResponse[list[PackageProductResponse]],
    summary="List packages available for purchase",
)
async def list_packages(
    controller: PackageController = Depends(get_package_controller),
) -> ApiResponse[list[PackageProductResponse]]:
    return await controller.list_products()


@router.post(
    "",
    response_model=ApiResponse[PackageProductResponse],
    status_code=201,
    summary="Create a new package product (Admin/Staff only)",
)
async def create_package_product(
    req: CreatePackageProductRequest,
    _current_user: UserInDB = Depends(
        require_roles(UserRole.ADMIN, UserRole.SUPER_ADMIN, UserRole.STAFF)
    ),
    controller: PackageController = Depends(get_package_controller),
) -> ApiResponse[PackageProductResponse]:
    return await controller.create_product(req)


@router.get(
    "/my",
    response_model=ApiResponse[list[UserPackageResponse]],
    summary="List packages owned by current user",
)
async def list_my_packages(
    current_user: UserInDB = Depends(get_current_active_user),
    controller: PackageController = Depends(get_package_controller),
) -> ApiResponse[list[UserPackageResponse]]:
    return await controller.list_my_packages(caller=current_user)


@router.get(
    "/my/usable",
    response_model=ApiResponse[list[UserPackageResponse]],
    summary="List unexpired packages with positive session balance for current user",
)
async def list_my_usable_packages(
    current_user: UserInDB = Depends(get_current_active_user),
    controller: PackageController = Depends(get_package_controller),
) -> ApiResponse[list[UserPackageResponse]]:
    return await controller.list_my_usable_packages(caller=current_user)


@router.get(
    "/{product_id}",
    response_model=ApiResponse[PackageProductResponse],
    summary="Get package product detail",
)
async def get_package(
    product_id: str,
    controller: PackageController = Depends(get_package_controller),
) -> ApiResponse[PackageProductResponse]:
    return await controller.get_product(product_id)
