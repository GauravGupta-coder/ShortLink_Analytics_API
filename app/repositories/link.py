from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from app.models.link import Link
from typing import List, Tuple

class LinkRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, link: Link) -> Link:
        self.db.add(link)
        await self.db.commit()
        await self.db.refresh(link)
        return link

    async def get_by_id(self, link_id: int) -> Link | None:
        result = await self.db.execute(select(Link).where(Link.id == link_id))
        return result.scalars().first()

    async def get_by_short_code(self, short_code: str) -> Link | None:
        result = await self.db.execute(select(Link).where(Link.short_code == short_code))
        return result.scalars().first()

    async def list_by_user(self, user_id: int, skip: int = 0, limit: int = 100) -> Tuple[List[Link], int]:
        result = await self.db.execute(
            select(Link).where(Link.user_id == user_id).offset(skip).limit(limit)
        )
        links = result.scalars().all()
        
        count_result = await self.db.execute(
            select(func.count(Link.id)).where(Link.user_id == user_id)
        )
        total = count_result.scalar_one()
        
        return list(links), total

    async def update(self, link: Link) -> Link:
        await self.db.commit()
        await self.db.refresh(link)
        return link

    async def delete(self, link: Link) -> None:
        await self.db.delete(link)
        await self.db.commit()
