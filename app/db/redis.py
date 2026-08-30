import redis.asyncio as redis
from app.core.config import settings

# Create redis connection pool
redis_client = redis.from_url(
    str(settings.REDIS_URL),
    encoding="utf-8",
    decode_responses=True
)

async def get_redis():
    """
    Dependency to get the redis connection.
    """
    try:
        yield redis_client
    finally:
        pass # Redis client pool handles connections automatically
