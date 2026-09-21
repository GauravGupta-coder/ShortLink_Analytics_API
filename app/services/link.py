import string
import secrets
from datetime import datetime, timezone
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from redis.asyncio import Redis

from app.schemas.link import LinkCreate
from app.models.link import Link
from app.repositories.link import LinkRepository

SHORT_CODE_LENGTH = 7
ALPHABET = string.ascii_letters + string.digits
CACHE_PREFIX = "shortlink:"
CACHE_EXPIRY = 3600  # 1 hour

def generate_short_code(length: int = SHORT_CODE_LENGTH) -> str:
    return ''.join(secrets.choice(ALPHABET) for _ in range(length))

class LinkService:
    def __init__(self, db: AsyncSession, redis: Redis):
        self.repo = LinkRepository(db)
        self.redis = redis

    async def create_link(self, link_in: LinkCreate, user_id: int) -> Link:
        max_retries = 5
        for _ in range(max_retries):
            short_code = generate_short_code()
            new_link = Link(
                user_id=user_id,
                original_url=str(link_in.original_url),
                short_code=short_code,
                expires_at=link_in.expires_at
            )
            try:
                return await self.repo.create(new_link)
            except IntegrityError:
                await self.repo.db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not generate a unique short code."
        )

    async def get_link(self, link_id: int, user_id: int) -> Link:
        link = await self.repo.get_by_id(link_id)
        if not link or link.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Link not found"
            )
        return link

    async def list_links(self, user_id: int, skip: int = 0, limit: int = 100) -> tuple[list[Link], int]:
        return await self.repo.list_by_user(user_id, skip=skip, limit=limit)

    async def delete_link(self, link_id: int, user_id: int) -> None:
        link = await self.get_link(link_id, user_id)
        # Delete from DB
        await self.repo.delete(link)
        # Invalidate cache
        try:
            from redis.asyncio import RedisError
            await self.redis.delete(f"{CACHE_PREFIX}{link.short_code}")
        except Exception:
            pass # Ignore redis errors on delete

    async def resolve_short_code(self, short_code: str) -> tuple[str, int]:
        cache_key = f"{CACHE_PREFIX}{short_code}"
        
        # 1. Check Redis
        try:
            cached_data = await self.redis.get(cache_key)
            if cached_data:
                try:
                    data = json.loads(cached_data)
                    return data["url"], data["id"]
                except (json.JSONDecodeError, KeyError):
                    pass # Fallback to DB if cache is malformed or old string format
        except Exception:
            pass # Fallback to DB if redis fails

        # 2. Check DB
        link = await self.repo.get_by_short_code(short_code)
        
        if not link:
            raise HTTPException(status_code=404, detail="Short code not found")
            
        if not link.is_active:
            raise HTTPException(status_code=404, detail="Link is deactivated")
        if link.expires_at and link.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            raise HTTPException(status_code=410, detail="Link has expired")

        # 3. Cache the result as JSON
        try:
            cache_value = json.dumps({"url": link.original_url, "id": link.id})
            await self.redis.set(cache_key, cache_value, ex=CACHE_EXPIRY)
        except Exception:
            pass # Ignore redis failure

        return link.original_url, link.id
