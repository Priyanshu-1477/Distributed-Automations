import redis.asyncio as aioredis

from src.core.config import get_settings

_redis_client: aioredis.Redis | None = None


def get_redis_client() -> aioredis.Redis:
    """Returns or initializes the async Redis client singleton."""
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


async def check_redis_health() -> bool:
    """Performs a PING command to verify Redis connectivity."""
    try:
        client = get_redis_client()
        pong = await client.ping()
        return pong is True or pong == "PONG"
    except Exception:
        return False


async def close_redis_client() -> None:
    """Closes the Redis client connection pool."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
