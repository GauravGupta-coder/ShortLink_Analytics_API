import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from app.models.user import User
from tests.api.test_links import get_mock_link
from app.models.analytics import Click

def get_mock_click(id=1, link_id=1):
    return Click(
        id=id,
        link_id=link_id,
        clicked_at=datetime.now(timezone.utc),
        ip_address="127.0.0.1",
        browser="Chrome",
        operating_system="Windows",
        device_type="desktop",
        referrer="https://google.com"
    )

@pytest.mark.asyncio
async def test_get_link_analytics_success(async_client: AsyncClient, auth_headers):
    with patch("app.repositories.link.LinkRepository.get_by_id") as mock_get_link, \
         patch("app.repositories.user.UserRepository.get_by_id") as mock_get_user, \
         patch("app.repositories.analytics.AnalyticsRepository.get_total_clicks") as mock_total, \
         patch("app.repositories.analytics.AnalyticsRepository.get_clicks_since") as mock_since, \
         patch("app.repositories.analytics.AnalyticsRepository.get_recent_clicks") as mock_recent:
        
        mock_get_user.return_value = User(id=1, email="test@example.com")
        mock_get_link.return_value = get_mock_link(id=1, user_id=1)
        
        mock_total.return_value = 100
        mock_since.side_effect = [10, 50, 90] # today, 7d, 30d
        mock_recent.return_value = [get_mock_click(id=1, link_id=1), get_mock_click(id=2, link_id=1)]

        response = await async_client.get("/api/v1/links/1/analytics", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_clicks"] == 100
        assert data["clicks_today"] == 10
        assert data["clicks_last_7_days"] == 50
        assert len(data["recent_clicks"]) == 2

@pytest.mark.asyncio
async def test_get_analytics_unauthorized(async_client: AsyncClient, auth_headers):
    with patch("app.repositories.link.LinkRepository.get_by_id") as mock_get_link, \
         patch("app.repositories.user.UserRepository.get_by_id") as mock_get_user:
        
        mock_get_user.return_value = User(id=1, email="test@example.com")
        mock_get_link.return_value = get_mock_link(id=1, user_id=2) # Belongs to user 2

        response = await async_client.get("/api/v1/links/1/analytics", headers=auth_headers)
        assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_timeline_success(async_client: AsyncClient, auth_headers):
    with patch("app.repositories.link.LinkRepository.get_by_id") as mock_get_link, \
         patch("app.repositories.user.UserRepository.get_by_id") as mock_get_user, \
         patch("app.repositories.analytics.AnalyticsRepository.get_timeline") as mock_timeline:
        
        mock_get_user.return_value = User(id=1, email="test@example.com")
        mock_get_link.return_value = get_mock_link(id=1, user_id=1)
        mock_timeline.return_value = [{"date": "2023-01-01", "clicks": 5}]

        response = await async_client.get("/api/v1/links/1/analytics/timeline", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["timeline"]) == 1
        assert data["timeline"][0]["clicks"] == 5

@pytest.mark.asyncio
async def test_redirect_records_click(async_client: AsyncClient, mock_redis_client):
    with patch("app.repositories.link.LinkRepository.get_by_short_code") as mock_get_by_code, \
         patch("app.services.analytics.AnalyticsService.record_click") as mock_record:
        
        mock_get_by_code.return_value = get_mock_link(id=99)

        response = await async_client.get("/abcdefg", follow_redirects=False, headers={"User-Agent": "test-agent"})
        assert response.status_code == 307
        assert response.headers["location"] == "https://example.com"
        # Background task should have been added
        mock_record.assert_called_once_with(
            link_id=99,
            ip_address="127.0.0.1",
            user_agent_str="test-agent",
            referrer=""
        )
