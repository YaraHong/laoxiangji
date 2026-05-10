import redis.asyncio as aioredis

from app.core.config import settings
from app.core.logger_handle import logger

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        logger.info("连接 Redis: %s", settings.redis.url)
        _redis = aioredis.from_url(settings.redis.url, decode_responses=True)
    return _redis
