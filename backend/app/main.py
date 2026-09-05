"""FastAPI Application Factory with lifespan management."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_v1_router
from app.common.responses.api_response import ApiResponse, success_response
from app.core.config import get_settings
from app.core.logging import logger, setup_logging
from app.database.mongodb import mongo_manager
from app.middleware.middleware_config import setup_middlewares
from app.middleware.request_id_middleware import get_request_id


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown lifecycle safely."""
    # Startup
    setup_logging()
    logger.info("Initializing Oppam Platform Backend application...")
    await mongo_manager.connect()
    if mongo_manager.db is not None:
        try:
            from app.modules.auth.auth_repository import AuthRepository
            from app.modules.user.user_repository import UserRepository

            await UserRepository(mongo_manager.db).ensure_indexes()
            await AuthRepository(mongo_manager.db).ensure_indexes()
            logger.info("Database indexes initialized.")
        except Exception as exc:
            logger.warning("Database index creation deferred: %s", exc)
    logger.info("Application startup lifecycle complete.")

    yield

    # Shutdown
    logger.info("Executing application shutdown sequence...")
    await mongo_manager.disconnect()
    logger.info("Application shutdown complete.")


def create_app() -> FastAPI:
    """Construct and configure the production FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs" if settings.debug or settings.app_env != "production" else None,
        redoc_url="/redoc" if settings.debug or settings.app_env != "production" else None,
        openapi_url="/openapi.json" if settings.debug or settings.app_env != "production" else None,
        lifespan=lifespan,
    )

    # Attach all middleware & exception handlers
    setup_middlewares(app)

    # Register API v1 router
    app.include_router(api_v1_router)

    # Root endpoint
    @app.get("/", response_model=ApiResponse[dict[str, str]], include_in_schema=False)
    async def root() -> ApiResponse[dict[str, str]]:
        return success_response(
            data={"name": settings.app_name, "version": settings.app_version},
            message="Oppam Counselling Platform API service is running",
            request_id=get_request_id(),
        )

    return app


app = create_app()
