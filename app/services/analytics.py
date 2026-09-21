import json
import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from user_agents import parse

from app.repositories.analytics import AnalyticsRepository
from app.schemas.analytics import AnalyticsResponse, TimelineResponse
from app.services.link import LinkService
from redis.asyncio import Redis

logger = logging.getLogger(__name__)

class AnalyticsService:
    def __init__(self, db: AsyncSession, redis: Redis = None):
        self.repo = AnalyticsRepository(db)
        self.db = db
        self.redis = redis

    async def record_click(self, link_id: int, ip_address: str, user_agent_str: str, referrer: str):
        """
        Record a click asynchronously without blocking the redirect.
        """
        try:
            # Parse user agent
            browser = None
            operating_system = None
            device_type = None
            
            if user_agent_str:
                user_agent = parse(user_agent_str)
                browser = user_agent.browser.family
                operating_system = user_agent.os.family
                if user_agent.is_mobile:
                    device_type = "mobile"
                elif user_agent.is_tablet:
                    device_type = "tablet"
                elif user_agent.is_pc:
                    device_type = "desktop"
                elif user_agent.is_bot:
                    device_type = "bot"

            click_data = {
                "link_id": link_id,
                "ip_address": ip_address,
                "user_agent": user_agent_str,
                "referrer": referrer,
                "browser": browser,
                "operating_system": operating_system,
                "device_type": device_type
            }
            
            await self.repo.create_click(click_data)
        except Exception as e:
            # We catch all exceptions so the redirect doesn't fail
            # Just log the error
            logger.error(f"Failed to record click for link {link_id}: {e}")

    async def get_analytics_for_link(self, link_id: int, user_id: int) -> AnalyticsResponse:
        # Verify ownership
        link_service = LinkService(self.db, self.redis)
        await link_service.get_link(link_id, user_id) # Raises 404 if not found or unauthorized

        total_clicks = await self.repo.get_total_clicks(link_id)
        
        now = datetime.now(timezone.utc)
        clicks_today = await self.repo.get_clicks_since(link_id, now - timedelta(days=1))
        clicks_last_7_days = await self.repo.get_clicks_since(link_id, now - timedelta(days=7))
        clicks_last_30_days = await self.repo.get_clicks_since(link_id, now - timedelta(days=30))
        
        recent_clicks = await self.repo.get_recent_clicks(link_id, limit=10)
        recent_clicks_dict = [
            {
                "id": c.id,
                "clicked_at": c.clicked_at.isoformat(),
                "ip_address": c.ip_address,
                "browser": c.browser,
                "operating_system": c.operating_system,
                "device_type": c.device_type,
                "referrer": c.referrer
            }
            for c in recent_clicks
        ]

        return AnalyticsResponse(
            link_id=link_id,
            total_clicks=total_clicks,
            clicks_today=clicks_today,
            clicks_last_7_days=clicks_last_7_days,
            clicks_last_30_days=clicks_last_30_days,
            recent_clicks=recent_clicks_dict
        )

    async def get_timeline_for_link(self, link_id: int, user_id: int, days: int = 30) -> TimelineResponse:
        # Verify ownership
        link_service = LinkService(self.db, self.redis)
        await link_service.get_link(link_id, user_id)

        timeline = await self.repo.get_timeline(link_id, days)
        return TimelineResponse(
            link_id=link_id,
            timeline=timeline
        )
