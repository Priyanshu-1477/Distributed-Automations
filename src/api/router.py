from fastapi import APIRouter

from src.api.v1.health import router as health_router

api_v1_router = APIRouter()

# Include health routes
api_v1_router.include_router(health_router)
