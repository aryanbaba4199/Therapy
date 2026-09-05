"""Central API Version 1 router registration."""

from fastapi import APIRouter

from app.api.v1.endpoints import health
from app.modules.auth.auth_route import router as auth_router
from app.modules.availability.availability_route import router as availability_router
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

