"""System health and telemetry check endpoints."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.common.responses.api_response import ApiResponse, success_response
from app.core.config import get_settings
from app.database.mongodb import mongo_manager
from app.middleware.request_id_middleware import get_request_id

router = APIRouter(tags=["Health"])


class DatabaseHealth(BaseModel):
    """Status of database connectivity."""

    connected: bool
    status: str


class HealthData(BaseModel):
    """Standard system health status response payload."""

    status: str = Field(default="healthy", description="Overall platform operational state")
    environment: str = Field(description="Running environment name")
    version: str = Field(description="Application version number")
    database: DatabaseHealth = Field(description="Database connectivity diagnostics")


@router.get(
    "/health",
    response_model=ApiResponse[HealthData],
    summary="Platform Health Check",
    description="Returns current operational status, environment diagnostics, and database health.",
)
async def health_check() -> ApiResponse[HealthData]:
    """Execute health checks and return standardized envelope."""
    settings = get_settings()
    db_connected = await mongo_manager.ping()

    payload = HealthData(
        status="healthy" if db_connected else "degraded",
        environment=settings.app_env,
        version=settings.app_version,
        database=DatabaseHealth(
            connected=db_connected,
            status="connected" if db_connected else "disconnected",
        ),
    )

    req_id = get_request_id()
    return success_response(
        data=payload,
        message="Platform health check completed",
        request_id=req_id,
    )
