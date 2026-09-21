from fastapi import Request, HTTPException, status, Depends
from redis.asyncio import Redis, RedisError
import logging
from app.api.dependencies import get_redis

logger = logging.getLogger(__name__)

def RateLimiter(times: int, seconds: int = 60):
    """
    Rate limiting dependency using Redis.
    If Redis fails, it fails open (allows the request) to avoid disrupting the service.
    """
    async def _rate_limiter(request: Request, redis: Redis = Depends(get_redis)):
        client_ip = request.client.host if request.client else "127.0.0.1"
        key = f"rate_limit:{request.url.path}:{client_ip}"
        
        try:
            current = await redis.get(key)
            if current and int(current) >= times:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too Many Requests"
                )
            
            pipe = redis.pipeline()
            pipe.incr(key)
            pipe.expire(key, seconds)
            await pipe.execute()
        except RedisError as e:
            logger.warning(f"Redis error in rate limiter for {key}: {e}")
            # Fail open
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in rate limiter: {e}")
            # Fail open
            
    return _rate_limiter
