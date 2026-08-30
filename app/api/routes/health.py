from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from redis.asyncio import Redis
import logging

from app.api.dependencies import get_db, get_redis
from app.schemas.health import HealthResponse

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/health", response_model=HealthResponse)
async def health_check(
    db: AsyncSession = Depends(get_db),
    redis_client: Redis = Depends(get_redis)
):
    """
    Check the health of the API and its dependencies (PostgreSQL, Redis).
    """
    postgres_status = "ok"
    redis_status = "ok"

    # Check PostgreSQL
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}")
        postgres_status = "error"

    # Check Redis
    try:
        await redis_client.ping()
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        redis_status = "error"

    overall_status = "ok" if postgres_status == "ok" and redis_status == "ok" else "error"

    return HealthResponse(
        status=overall_status,
        postgres=postgres_status,
        redis=redis_status
    )
