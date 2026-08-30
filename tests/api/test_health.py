import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_health_check_success(async_client: AsyncClient):
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["postgres"] == "ok"
    assert data["redis"] == "ok"

@pytest.mark.asyncio
async def test_health_check_postgres_failure(async_client: AsyncClient, mock_db_session):
    # Mock a failure
    async def mock_execute(*args, **kwargs):
        raise Exception("DB Down")
    mock_db_session.execute = mock_execute
    
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert data["postgres"] == "error"
    assert data["redis"] == "ok"

@pytest.mark.asyncio
async def test_health_check_redis_failure(async_client: AsyncClient, mock_redis_client):
    # Mock a failure
    async def mock_ping():
        raise Exception("Redis Down")
    mock_redis_client.ping = mock_ping
    
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "error"
    assert data["postgres"] == "ok"
    assert data["redis"] == "error"
