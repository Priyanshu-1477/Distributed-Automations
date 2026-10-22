from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from src.api.router import api_v1_router
from src.api.v1.health import router as health_router
from src.core.config import get_settings
from src.core.exceptions import (
    DispatchError,
    DomainError,
    EntityNotFoundError,
    InvalidStateTransitionError,
    OptimisticLockError,
)
from src.core.logging import get_logger, setup_logging
from src.core.redis import close_redis_client

logger = get_logger("orchestrator.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan manager for FastAPI application startup and shutdown."""
    setup_logging()
    logger.info("Starting Distributed Automation Platform Orchestrator...")
    yield
    logger.info("Shutting down Orchestrator; releasing resources...")
    await close_redis_client()
    logger.info("Shutdown complete.")


def create_app() -> FastAPI:
    """Application factory for the FastAPI orchestrator service."""
    settings = get_settings()

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version="0.1.0",
        description=(
            "Distributed Task Automation Platform featuring FastAPI, Celery, Redis, "
            "PostgreSQL, and optimistic state machine controls."
        ),
        lifespan=lifespan,
    )

    # Global Exception Handlers
    @app.exception_handler(EntityNotFoundError)
    async def entity_not_found_handler(request: Request, exc: EntityNotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": "Not Found", "message": exc.message, "details": exc.details},
        )

    @app.exception_handler(InvalidStateTransitionError)
    async def state_transition_handler(
        request: Request, exc: InvalidStateTransitionError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"error": "Conflict", "message": exc.message, "details": exc.details},
        )

    @app.exception_handler(OptimisticLockError)
    async def optimistic_lock_handler(request: Request, exc: OptimisticLockError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"error": "Conflict", "message": exc.message, "details": exc.details},
        )

    @app.exception_handler(DispatchError)
    async def dispatch_error_handler(request: Request, exc: DispatchError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": "Service Unavailable",
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Bad Request", "message": exc.message, "details": exc.details},
        )

    # Mount routers
    app.include_router(health_router)  # /health/live and /health/ready at root
    app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

    return app


app = create_app()
