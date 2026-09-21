import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator

from app.main import app
from app.api.dependencies import get_db, get_redis
from app.core.config import settings
from app.core.security import create_access_token

# We could use a separate test DB here, but for simplicity of Phase 1, 
# we'll mock the dependencies or use the dev DB if isolated.
# Let's mock the DB and Redis for simple endpoint testing.

class MockAsyncSession:
    async def execute(self, *args, **kwargs):
        pass

class MockRedis:
    def __init__(self):
        self.data = {}

    async def ping(self):
        return True

    async def get(self, name):
        return self.data.get(name)

    async def set(self, name, value, ex=None):
        self.data[name] = value

    async def delete(self, name):
        if name in self.data:
            del self.data[name]

    def pipeline(self):
        class MockPipeline:
            def __init__(self, redis_client):
                self.redis_client = redis_client

            def incr(self, name):
                if name not in self.redis_client.data:
                    self.redis_client.data[name] = "0"
                self.redis_client.data[name] = str(int(self.redis_client.data[name]) + 1)

            def expire(self, name, time):
                pass

            async def execute(self):
                pass
        return MockPipeline(self)

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

@pytest.fixture
def auth_headers():
    token = create_access_token(subject=1)
    return {"Authorization": f"Bearer {token}"}
