from fastapi import APIRouter, Response, status
from pydantic import BaseModel

from src.core.database import check_database_health
from src.core.redis import check_redis_health

router = APIRouter(prefix="/health", tags=["Health & Readiness"])


class ComponentHealth(BaseModel):
    database: bool
    redis: bool


class HealthStatusResponse(BaseModel):
    status: str
    components: ComponentHealth


class LivenessResponse(BaseModel):
    status: str


@router.get(
    "/live",
    response_model=LivenessResponse,
    status_code=status.HTTP_200_OK,
    summary="Application liveness probe",
    description="Returns 200 OK if the orchestrator process is alive and accepting traffic.",
)
async def liveness_check() -> LivenessResponse:
    return LivenessResponse(status="alive")


@router.get(
    "/ready",
    response_model=HealthStatusResponse,
    summary="Application readiness probe",
    description="Verifies downstream dependencies (PostgreSQL and Redis) are connected and responsive.",
)
async def readiness_check(response: Response) -> HealthStatusResponse:
    db_healthy = await check_database_health()
    redis_healthy = await check_redis_health()

    is_ready = db_healthy and redis_healthy
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthStatusResponse(
        status="ready" if is_ready else "unhealthy",
        components=ComponentHealth(
            database=db_healthy,
            redis=redis_healthy,
        ),
    )
