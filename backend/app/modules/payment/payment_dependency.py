"""Dependency injection for Payment module."""

from typing import Any

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.config import Settings, get_settings
from app.database.mongodb import get_database
from app.modules.booking.booking_dependency import get_booking_repository, get_booking_service
from app.modules.booking.booking_repository import BookingRepository
from app.modules.booking.booking_service import BookingService
from app.modules.offer.offer_dependency import get_offer_service
from app.modules.offer.offer_service import OfferService
from app.modules.package.package_dependency import get_package_service
from app.modules.package.package_service import PackageService
from app.modules.payment.payment_provider import (
    MockPaymentProvider,
    PaymentProvider,
    RazorpayPaymentProvider,
)
from app.modules.payment.payment_repository import PaymentRepository
from app.modules.payment.payment_service import PaymentService


def get_payment_repository(
    db: AsyncIOMotorDatabase[dict[str, Any]] = Depends(get_database),
) -> PaymentRepository:
    return PaymentRepository(db=db)


def get_payment_provider(
    settings: Settings = Depends(get_settings),
) -> PaymentProvider:
    if settings.payment_provider == "razorpay":
        return RazorpayPaymentProvider(
            key_id=settings.razorpay_key_id,
            key_secret=settings.razorpay_key_secret,
            webhook_secret=settings.razorpay_webhook_secret,
        )
    return MockPaymentProvider(secret_key=settings.payment_webhook_secret)


def get_payment_service(
    payment_repo: PaymentRepository = Depends(get_payment_repository),
    booking_repo: BookingRepository = Depends(get_booking_repository),
    booking_service: BookingService = Depends(get_booking_service),
    offer_service: OfferService = Depends(get_offer_service),
    package_service: PackageService = Depends(get_package_service),
    settings: Settings = Depends(get_settings),
    provider: PaymentProvider = Depends(get_payment_provider),
) -> PaymentService:
    return PaymentService(
        payment_repo=payment_repo,
        booking_repo=booking_repo,
        booking_service=booking_service,
        offer_service=offer_service,
        package_service=package_service,
        settings=settings,
        provider=provider,
    )
