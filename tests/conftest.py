import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator

from app.main import app
from app.api.dependencies import get_db, get_redis
from app.core.config import settings
import redis.asyncio as redis

# We could use a separate test DB here, but for simplicity of Phase 1, 
# we'll mock the dependencies or use the dev DB if isolated.
# Let's mock the DB and Redis for simple endpoint testing.

class MockAsyncSession:
    async def execute(self, *args, **kwargs):
        pass

class MockRedis:
    async def ping(self):
        return True

@pytest.fixture
def mock_db_session():
    return MockAsyncSession()

@pytest.fixture
def mock_redis_client():
    return MockRedis()

@pytest_asyncio.fixture
async def async_client(mock_db_session, mock_redis_client) -> AsyncGenerator[AsyncClient, None]:
    
    async def override_get_db():
        yield mock_db_session

    async def override_get_redis():
        yield mock_redis_client

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client
        
    app.dependency_overrides.clear()
