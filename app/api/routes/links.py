from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.api.dependencies import get_db, get_redis, get_current_user
from app.models.user import User
from app.schemas.link import LinkCreate, LinkResponse, LinkListResponse
from app.services.link import LinkService

router = APIRouter()

def get_link_service(db: AsyncSession = Depends(get_db), redis: Redis = Depends(get_redis)) -> LinkService:
    return LinkService(db, redis)

@router.post("", response_model=LinkResponse, status_code=status.HTTP_201_CREATED)
async def create_link(
    link_in: LinkCreate,
    current_user: User = Depends(get_current_user),
    link_service: LinkService = Depends(get_link_service)
):
    """
    Creates a new short link for the authenticated user.
    
    Generates a unique, collision-resistant 7-character short code.
    """
    return await link_service.create_link(link_in, user_id=current_user.id)

@router.get("", response_model=LinkListResponse)
async def list_links(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    link_service: LinkService = Depends(get_link_service)
):
    """
    Retrieves a paginated list of all short links created by the authenticated user.
    """
    links, total = await link_service.list_links(user_id=current_user.id, skip=skip, limit=limit)
    return {"items": links, "total": total}

@router.get("/{link_id}", response_model=LinkResponse)
async def get_link(
    link_id: int,
    current_user: User = Depends(get_current_user),
    link_service: LinkService = Depends(get_link_service)
):
    """
    Retrieves the details of a specific short link owned by the user.
    """
    return await link_service.get_link(link_id, user_id=current_user.id)

@router.delete("/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_link(
    link_id: int,
    current_user: User = Depends(get_current_user),
    link_service: LinkService = Depends(get_link_service)
):
    """
    Permanently deletes a specific short link and cascades the deletion to all associated analytics.
    """
    await link_service.delete_link(link_id, user_id=current_user.id)
