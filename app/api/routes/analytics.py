from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.api.dependencies import get_db, get_redis, get_current_user
from app.models.user import User
from app.schemas.analytics import AnalyticsResponse, TimelineResponse
from app.services.analytics import AnalyticsService

router = APIRouter()

@router.get("/{link_id}/analytics", response_model=AnalyticsResponse)
async def get_link_analytics(
    link_id: int,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves aggregated analytics for a specific short link.
    
    Includes total clicks, top referrers, and top user agents.
    Requires ownership of the link.
    """
    analytics_service = AnalyticsService(db, redis)
    return await analytics_service.get_analytics_for_link(link_id, current_user.id)

@router.get("/{link_id}/analytics/timeline", response_model=TimelineResponse)
async def get_link_analytics_timeline(
    link_id: int,
    days: int = 30,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves a time-series aggregation of clicks for a specific short link.
    
    Returns a daily breakdown of clicks over the specified number of `days` (default 30).
    Requires ownership of the link.
    """
    analytics_service = AnalyticsService(db, redis)
    return await analytics_service.get_timeline_for_link(link_id, current_user.id, days)
