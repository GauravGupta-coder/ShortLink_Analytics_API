from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional

class LinkCreate(BaseModel):
    original_url: HttpUrl
    expires_at: Optional[datetime] = None

class LinkResponse(BaseModel):
    id: int
    user_id: int
    original_url: str
    short_code: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class LinkListResponse(BaseModel):
    items: list[LinkResponse]
    total: int
