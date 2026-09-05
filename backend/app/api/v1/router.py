"""Central API Version 1 router registration."""

from fastapi import APIRouter

from app.api.v1.endpoints import health

api_v1_router = APIRouter(prefix="/api/v1")

# Core system routes
api_v1_router.include_router(health.router)

# ==============================================================================
# Future Feature Module Routes
#
# When implementing future feature modules, register routers here:
#
# from app.modules.auth.auth_route import router as auth_router
# from app.modules.therapist.therapist_route import router as therapist_router
# from app.modules.booking.booking_route import router as booking_router
#
# api_v1_router.include_router(auth_router, prefix="/auth", tags=["Auth"])
# api_v1_router.include_router(therapist_router, prefix="/therapists", tags=["Therapists"])
# api_v1_router.include_router(booking_router, prefix="/booking", tags=["Booking"])
# ==============================================================================
