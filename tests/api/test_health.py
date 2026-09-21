import pytest
from httpx import AsyncClient
from unittest.mock import patch

@pytest.mark.asyncio
async def test_health_check_success(async_client: AsyncClient):
    response = await async_client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_readiness_check_success(async_client: AsyncClient, mock_redis_client):
    response = await async_client.get("/api/v1/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["postgres"] == "ok"
    assert data["redis"] == "ok"

@pytest.mark.asyncio
async def test_readiness_check_postgres_failure(async_client: AsyncClient, mock_db_session):
    async def mock_execute(*args, **kwargs):
        raise Exception("DB Down")
    mock_db_session.execute = mock_execute
    
    response = await async_client.get("/api/v1/ready")
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "error"
    assert data["postgres"] == "error"

@pytest.mark.asyncio
async def test_readiness_check_redis_failure(async_client: AsyncClient, mock_redis_client):
    async def mock_ping():
        raise Exception("Redis Down")
    mock_redis_client.ping = mock_ping
    
    response = await async_client.get("/api/v1/ready")
    assert response.status_code == 200 # Should return 200 with degraded status if only redis is down
    data = response.json()
    assert data["status"] == "error"
    assert data["postgres"] == "ok"
    assert data["redis"] == "error"
