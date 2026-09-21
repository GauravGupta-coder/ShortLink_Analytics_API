import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
from datetime import datetime, timedelta, timezone
from app.models.link import Link
from app.models.user import User
from app.core.security import create_access_token

def get_mock_link(id=1, user_id=1, short_code="abcdefg", is_active=True, expires=False):
    return Link(
        id=id,
        user_id=user_id,
        original_url="https://example.com",
        short_code=short_code,
        is_active=is_active,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) - timedelta(days=1) if expires else None
    )

@pytest.fixture
def auth_headers():
    token = create_access_token(subject=1)
    return {"Authorization": f"Bearer {token}"}

@pytest.mark.asyncio
async def test_create_link_success(async_client: AsyncClient, auth_headers):
    with patch("app.repositories.link.LinkRepository.create") as mock_create, \
         patch("app.repositories.user.UserRepository.get_by_id") as mock_get_user:
        
        mock_get_user.return_value = User(id=1, email="test@example.com")
        mock_create.return_value = get_mock_link()

        response = await async_client.post(
            "/api/v1/links",
            json={"original_url": "https://example.com"},
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["original_url"] == "https://example.com"
        assert data["short_code"] == "abcdefg"

@pytest.mark.asyncio
async def test_create_link_invalid_url(async_client: AsyncClient, auth_headers):
    with patch("app.repositories.user.UserRepository.get_by_id") as mock_get_user:
        mock_get_user.return_value = User(id=1, email="test@example.com")
        response = await async_client.post(
            "/api/v1/links",
            json={"original_url": "not-a-url"},
            headers=auth_headers
        )
        assert response.status_code == 422

@pytest.mark.asyncio
async def test_unauthenticated_access(async_client: AsyncClient):
    response = await async_client.get("/api/v1/links")
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_list_links(async_client: AsyncClient, auth_headers):
    with patch("app.repositories.link.LinkRepository.list_by_user") as mock_list, \
         patch("app.repositories.user.UserRepository.get_by_id") as mock_get_user:
        
        mock_get_user.return_value = User(id=1, email="test@example.com")
        mock_list.return_value = ([get_mock_link(id=1), get_mock_link(id=2)], 2)

        response = await async_client.get("/api/v1/links", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

@pytest.mark.asyncio
async def test_get_own_link(async_client: AsyncClient, auth_headers):
    with patch("app.repositories.link.LinkRepository.get_by_id") as mock_get, \
         patch("app.repositories.user.UserRepository.get_by_id") as mock_get_user:
        
        mock_get_user.return_value = User(id=1, email="test@example.com")
        mock_get.return_value = get_mock_link(user_id=1)

        response = await async_client.get("/api/v1/links/1", headers=auth_headers)
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_cannot_access_another_user_link(async_client: AsyncClient, auth_headers):
    with patch("app.repositories.link.LinkRepository.get_by_id") as mock_get, \
         patch("app.repositories.user.UserRepository.get_by_id") as mock_get_user:
        
        mock_get_user.return_value = User(id=1, email="test@example.com")
        mock_get.return_value = get_mock_link(user_id=2) # Belongs to user 2, token is for user 1

        response = await async_client.get("/api/v1/links/1", headers=auth_headers)
        assert response.status_code == 404

@pytest.mark.asyncio
async def test_delete_link(async_client: AsyncClient, auth_headers, mock_redis_client):
    with patch("app.repositories.link.LinkRepository.get_by_id") as mock_get, \
         patch("app.repositories.link.LinkRepository.delete") as mock_delete, \
         patch("app.repositories.user.UserRepository.get_by_id") as mock_get_user:
        
        mock_get_user.return_value = User(id=1, email="test@example.com")
        mock_get.return_value = get_mock_link(user_id=1)
        mock_redis_client.data["shortlink:abcdefg"] = '{"url": "https://example.com", "id": 1}'

        response = await async_client.delete("/api/v1/links/1", headers=auth_headers)
        assert response.status_code == 204
        mock_delete.assert_called_once()
        assert "shortlink:abcdefg" not in mock_redis_client.data

@pytest.mark.asyncio
async def test_redirect_existing_link_cache_miss(async_client: AsyncClient, mock_redis_client):
    with patch("app.repositories.link.LinkRepository.get_by_short_code") as mock_get_by_code:
        
        mock_get_by_code.return_value = get_mock_link()

        response = await async_client.get("/abcdefg", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "https://example.com"
        assert mock_redis_client.data["shortlink:abcdefg"] == '{"url": "https://example.com", "id": 1}'

@pytest.mark.asyncio
async def test_redirect_existing_link_cache_hit(async_client: AsyncClient, mock_redis_client):
    mock_redis_client.data["shortlink:abcdefg"] = '{"url": "https://cached-example.com", "id": 1}'
    response = await async_client.get("/abcdefg", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "https://cached-example.com"

@pytest.mark.asyncio
async def test_redirect_invalid_short_code(async_client: AsyncClient, mock_redis_client):
    with patch("app.repositories.link.LinkRepository.get_by_short_code") as mock_get_by_code:
        
        mock_get_by_code.return_value = None

        response = await async_client.get("/invalid", follow_redirects=False)
        assert response.status_code == 404

@pytest.mark.asyncio
async def test_redirect_inactive_link(async_client: AsyncClient, mock_redis_client):
    with patch("app.repositories.link.LinkRepository.get_by_short_code") as mock_get_by_code:
        
        mock_get_by_code.return_value = get_mock_link(is_active=False)

        response = await async_client.get("/abcdefg", follow_redirects=False)
        assert response.status_code == 404

@pytest.mark.asyncio
async def test_redirect_expired_link(async_client: AsyncClient, mock_redis_client):
    with patch("app.repositories.link.LinkRepository.get_by_short_code") as mock_get_by_code:
        
        mock_get_by_code.return_value = get_mock_link(expires=True)

        response = await async_client.get("/abcdefg", follow_redirects=False)
        assert response.status_code == 410
