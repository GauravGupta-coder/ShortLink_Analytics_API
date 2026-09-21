import pytest
from httpx import AsyncClient
from unittest.mock import patch
from datetime import datetime, timezone
from app.models.user import User
from app.core.security import get_password_hash

@pytest.mark.asyncio
async def test_register_user_success(async_client: AsyncClient):
    with patch("app.services.user.UserRepository.get_by_email") as mock_get_by_email, \
         patch("app.services.user.UserRepository.create") as mock_create:
        
        mock_get_by_email.return_value = None
        
        # Mock created user returned by create
        mock_user = User(
            id=1, 
            email="test@example.com", 
            password_hash="hashed", 
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        mock_create.return_value = mock_user

        response = await async_client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "password123"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "test@example.com"
        assert "id" in data

@pytest.mark.asyncio
async def test_register_user_existing_email(async_client: AsyncClient):
    with patch("app.services.user.UserRepository.get_by_email") as mock_get_by_email:
        
        mock_get_by_email.return_value = User(id=1, email="test@example.com")

        response = await async_client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "password123"}
        )
        
        assert response.status_code == 400
        assert response.json()["detail"] == "Email already registered"

@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient):
    with patch("app.services.user.UserRepository.get_by_email") as mock_get_by_email:
        
        # Mock valid user
        hashed_pw = get_password_hash("password123")
        mock_get_by_email.return_value = User(
            id=1, 
            email="test@example.com", 
            password_hash=hashed_pw, 
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )

        response = await async_client.post(
            "/api/v1/auth/login",
            data={"username": "test@example.com", "password": "password123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_register_invalid_email(async_client: AsyncClient):
    response = await async_client.post(
        "/api/v1/auth/register",
        json={"email": "not-an-email", "password": "password123"}
    )
    assert response.status_code == 422

@pytest.mark.asyncio
async def test_login_wrong_password(async_client: AsyncClient):
    with patch("app.services.user.UserRepository.get_by_email") as mock_get_by_email:
        hashed_pw = get_password_hash("password123")
        mock_get_by_email.return_value = User(
            id=1, 
            email="test@example.com", 
            password_hash=hashed_pw, 
            is_active=True
        )

        response = await async_client.post(
            "/api/v1/auth/login",
            data={"username": "test@example.com", "password": "wrongpassword"}
        )
        
        assert response.status_code == 401
        assert response.json()["detail"] == "Incorrect email or password"

@pytest.mark.asyncio
async def test_read_users_me_success(async_client: AsyncClient):
    from app.core.security import create_access_token
    token = create_access_token(subject=1)
    
    with patch("app.repositories.user.UserRepository.get_by_id") as mock_get_by_id:
        mock_get_by_id.return_value = User(
            id=1, 
            email="test@example.com", 
            password_hash="hashed", 
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )

        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        assert response.json()["email"] == "test@example.com"
