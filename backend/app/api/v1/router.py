"""Central API Version 1 router registration."""

from fastapi import APIRouter

from app.api.v1.endpoints import health
from app.modules.auth.auth_route import router as auth_router
from app.modules.availability.availability_route import router as availability_router
from app.modules.booking.booking_route import router as booking_router
from app.modules.offer.offer_route import router as offer_router
from app.modules.package.package_route import router as package_router
from app.modules.payment.payment_route import router as payment_router
from app.modules.therapist.therapist_route import router as therapist_router
from app.modules.user.user_route import router as user_router

api_v1_router = APIRouter(prefix="/api/v1")

# Core system routes
api_v1_router.include_router(health.router)

# Feature Module Routes
api_v1_router.include_router(auth_router)
api_v1_router.include_router(user_router)
api_v1_router.include_router(therapist_router)
api_v1_router.include_router(availability_router)
api_v1_router.include_router(booking_router)
api_v1_router.include_router(payment_router)
api_v1_router.include_router(offer_router)
api_v1_router.include_router(package_router)


