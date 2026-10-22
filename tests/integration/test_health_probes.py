from unittest.mock import patch

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_liveness_probe(client: AsyncClient):
    """Verify that the liveness probe returns HTTP 200."""
    response = await client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


@pytest.mark.asyncio
async def test_readiness_probe_healthy(client: AsyncClient):
    """Verify readiness returns 200 when all dependencies are healthy."""
    with (
        patch("src.api.v1.health.check_database_health", return_value=True),
        patch("src.api.v1.health.check_redis_health", return_value=True),
    ):
        response = await client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["components"]["database"] is True
        assert data["components"]["redis"] is True


@pytest.mark.asyncio
async def test_readiness_probe_database_unhealthy(client: AsyncClient):
    """Verify readiness returns 503 when the database check fails."""
    with (
        patch("src.api.v1.health.check_database_health", return_value=False),
        patch("src.api.v1.health.check_redis_health", return_value=True),
    ):
        response = await client.get("/health/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["components"]["database"] is False
        assert data["components"]["redis"] is True


@pytest.mark.asyncio
async def test_readiness_probe_redis_unhealthy(client: AsyncClient):
    """Verify readiness returns 503 when the Redis check fails."""
    with (
        patch("src.api.v1.health.check_database_health", return_value=True),
        patch("src.api.v1.health.check_redis_health", return_value=False),
    ):
        response = await client.get("/health/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["components"]["database"] is True
        assert data["components"]["redis"] is False
