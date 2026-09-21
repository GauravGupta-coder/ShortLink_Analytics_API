import pytest
from httpx import AsyncClient
from unittest.mock import patch
from redis.asyncio import RedisError
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone

@pytest.mark.asyncio
async def test_rate_limiter_exceeded(async_client: AsyncClient, mock_db_session, mock_redis_client):
    with patch("app.services.user.UserService.register_user") as mock_register:
        mock_register.return_value = {
            "id": 1,
            "email": "test@example.com",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }
        
        # In config, RATE_LIMIT_REGISTER is 5
        for _ in range(5):
            response = await async_client.post("/api/v1/auth/register", json={"email": "test@example.com", "password": "Password123!"})
            assert response.status_code == 201

        # 6th request should fail
        response = await async_client.post("/api/v1/auth/register", json={"email": "test@example.com", "password": "Password123!"})
        assert response.status_code == 429

@pytest.mark.asyncio
async def test_rate_limiter_redis_failure(async_client: AsyncClient, mock_db_session):
    with patch("app.services.user.UserService.register_user") as mock_register, \
         patch("tests.conftest.MockRedis.get", side_effect=RedisError("Redis is down")):
        
        mock_register.return_value = {
            "id": 1,
            "email": "test@example.com",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        }

        # Rate limiter should fail open
        response = await async_client.post("/api/v1/auth/register", json={"email": "test@example.com", "password": "Password123!"})
        assert response.status_code == 201

@pytest.mark.asyncio
async def test_sqlalchemy_exception_handler(async_client: AsyncClient):
    with patch("app.repositories.user.UserRepository.get_by_email", side_effect=SQLAlchemyError("DB went away")):
        response = await async_client.post("/api/v1/auth/login", data={"username": "test@example.com", "password": "Password123!"})
        assert response.status_code == 500
        assert response.json()["detail"] == "Internal Server Error"
