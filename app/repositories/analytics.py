from datetime import datetime, timedelta, timezone
from sqlalchemy import select, func, text, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict

from app.models.analytics import Click

class AnalyticsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_click(self, click_data: dict) -> Click:
        new_click = Click(**click_data)
        self.db.add(new_click)
        await self.db.commit()
        await self.db.refresh(new_click)
        return new_click

    async def get_total_clicks(self, link_id: int) -> int:
        result = await self.db.execute(
            select(func.count(Click.id)).where(Click.link_id == link_id)
        )
        return result.scalar_one()

    async def get_clicks_since(self, link_id: int, since: datetime) -> int:
        result = await self.db.execute(
            select(func.count(Click.id)).where(
                Click.link_id == link_id,
                Click.clicked_at >= since
            )
        )
        return result.scalar_one()

    async def get_recent_clicks(self, link_id: int, limit: int = 10) -> List[Click]:
        result = await self.db.execute(
            select(Click).where(Click.link_id == link_id).order_by(Click.clicked_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def get_timeline(self, link_id: int, days: int = 30) -> List[Dict]:
        since_date = datetime.now(timezone.utc) - timedelta(days=days)
        # Assuming PostgreSQL Date casting
        result = await self.db.execute(
            select(
                cast(Click.clicked_at, Date).label("date"),
                func.count(Click.id).label("clicks")
            ).where(
                Click.link_id == link_id,
                Click.clicked_at >= since_date
            ).group_by(
                cast(Click.clicked_at, Date)
            ).order_by(
                cast(Click.clicked_at, Date)
            )
        )
        
        timeline = []
        for row in result.all():
            timeline.append({
                "date": str(row.date),
                "clicks": row.clicks
            })
        return timeline
