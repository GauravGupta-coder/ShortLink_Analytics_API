from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from redis.asyncio import Redis
import logging

from app.api.dependencies import get_db, get_redis
from app.schemas.health import HealthResponse

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/health")
async def health_check():
    """
    Liveness probe.
    """
    return {"status": "ok"}

@router.get("/ready", response_model=HealthResponse)
async def readiness_check(
    db: AsyncSession = Depends(get_db),
    redis_client: Redis = Depends(get_redis)
):
    """
    Readiness probe - Check dependencies (PostgreSQL, Redis).
    """
    postgres_status = "ok"
    redis_status = "ok"

    # Check PostgreSQL
    try:
        await db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"PostgreSQL readiness check failed: {e}")
        postgres_status = "error"

    # Check Redis
    try:
        await redis_client.ping()
    except Exception as e:
        logger.error(f"Redis readiness check failed: {e}")
        redis_status = "error"

    overall_status = "ok" if postgres_status == "ok" and redis_status == "ok" else "error"

    response = HealthResponse(
        status=overall_status,
        postgres=postgres_status,
        redis=redis_status
    )
    
    # Return 503 if DB is down, otherwise 200 (even if Redis is down, we have DB fallback)
    from fastapi import Response
    if postgres_status == "error":
        return Response(content=response.model_dump_json(), status_code=503, media_type="application/json")
        
    return response
