# ShortLink Analytics API

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=flat&logo=fastapi)](https://fastapi.tiangolo.com/)

A high-performance URL shortener and click analytics engine built with Python, FastAPI, PostgreSQL, and Redis.

## The Problem

URL shortening services are common, but building one that remains highly available under heavy traffic while simultaneously capturing rich analytics without delaying user redirects is a significant architectural challenge.

The ShortLink Analytics API solves this by fully decoupling the redirect (read) path from the analytics (write) path. It utilizes a layered, asynchronous design where Redis handles rate-limiting and instantaneous cache resolution, while background processes securely record click telemetry to PostgreSQL.

## Project Overview

The ShortLink Analytics API is a robust URL shortening service that provides secure user authentication, rapid link redirection via caching, and asynchronous background analytics tracking. Designed to be scalable and developer-friendly, this API implements modern production standards including Rate Limiting, JWT Authorization, and comprehensive Docker containerization.

## Main Features

* **JWT Authentication**: Secure user registration, login, and token-based protected endpoints.
* **URL Shortening**: Collision-resistant, reliable short code generation.
* **Redis Caching**: Extremely fast redirects by retrieving active links directly from an in-memory Redis cache.
* **Click Analytics**: Asynchronous background tracking of every link click, logging IP address (anonymized/handled securely), User-Agent, and Referrer without blocking the redirect response.
* **Rate Limiting**: Redis-backed sliding window rate limiter that fails open to maintain availability during cache downtime.
* **PostgreSQL Persistence**: Fully asynchronous SQLAlchemy 2.0 ORM interactions with Alembic migrations.
* **Docker & CI/CD**: Ready to deploy with `docker-compose`, hardened non-root execution context, and automated GitHub Actions test pipelines.

## Technology Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12+)
- **Database**: PostgreSQL with `asyncpg` and SQLAlchemy 2.0
- **Cache & Rate Limiting**: Redis with `redis.asyncio`
- **Migrations**: Alembic
- **Testing**: Pytest, httpx
- **Containerization**: Docker & Docker Compose

## Architecture

The API uses a layered, asynchronous architecture:
- **Client** → Hits FastAPI endpoints.
- **FastAPI** → Handles routing, dependency injection (Rate Limiting, Auth, DB session).
- **Service Layer** → Contains the core business logic (e.g. `LinkService`, `AnalyticsService`).
- **Repository Layer** → Contains database queries and data abstraction.
- **PostgreSQL** → Source of truth for Users, Links, and Analytics data.
- **Redis** → Intercepts rate-limit checks and caches short link resolutions. Background tasks safely execute click tracking after a redirect response is sent.

For more details, see [Architecture Documentation](docs/architecture.md).

## Project Structure

```
├── app/
│   ├── api/          # FastAPI Routers & Dependencies
│   ├── core/         # Config, Exceptions, Logging, Security, Rate Limiting
│   ├── db/           # Async DB Engine & Redis Connection
│   ├── models/       # SQLAlchemy Models
│   ├── repositories/ # Database Access Methods
│   ├── schemas/      # Pydantic Schemas (Input/Output Validation)
│   └── services/     # Business Logic
├── tests/            # Pytest Suite
├── alembic/          # Database Migrations
├── .github/          # CI/CD Workflows
├── Dockerfile        # Production-hardened Image
├── docker-compose.yml# Local Development Stack
└── requirements.txt  # Python Dependencies
```

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
- Python 3.12+ (For local, non-Docker development)

## Local Setup

### 1. Environment Configuration

Copy the example environment file and configure the parameters:

```bash
cp .env.example .env
```

Ensure you change the `SECRET_KEY` and database passwords if adapting this for a public-facing deployment.

### 2. Docker Setup (Recommended)

Start the entire stack (API, PostgreSQL, Redis) via Docker Compose:

```bash
docker compose up -d --build
```

### 3. Database Migration Instructions

Once the containers are running, execute the initial Alembic migration to create the tables in PostgreSQL:

```bash
docker compose exec api alembic upgrade head
```

## Running the API

When running via Docker Compose, the API automatically binds to port 8000.
You can access it at: `http://localhost:8000`

## API Documentation

FastAPI automatically generates interactive OpenAPI documentation. Once the API is running, visit:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Workflows

### Authentication Flow
1. User registers at `POST /api/v1/auth/register` using an email and password.
2. User logs in at `POST /api/v1/auth/login` and receives a JWT Bearer token.
3. This token is passed as an `Authorization: Bearer <token>` header to access protected routes.

### Short-Link Flow
1. Authenticated user creates a link at `POST /api/v1/links/`.
2. The service generates a unique collision-free short code.
3. When a client visits `GET /{short_code}`, the API checks Redis. If not found, it checks Postgres, caches the result in Redis, and issues an HTTP 307 Redirect.

### Analytics Flow
1. During the `GET /{short_code}` request, FastAPI uses `BackgroundTasks` to delegate analytics tracking.
2. The HTTP 307 Redirect is returned to the user instantly.
3. The background task safely extracts request headers (IP, User-Agent, Referrer) and persists the click event in PostgreSQL.

## Example API Requests

### 1. Register a User
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
     -H "Content-Type: application/json" \
     -d '{"email":"user@example.com","password":"SecurePassword123!"}'
```

### 2. Create a Short Link
```bash
curl -X POST "http://localhost:8000/api/v1/links/" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"original_url":"https://github.com/developer/shortlink-analytics-api"}'
```

### 3. Retrieve Link Analytics
```bash
curl -X GET "http://localhost:8000/api/v1/analytics/1" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Example API Responses

**GET Link Analytics:**
```json
{
  "total_clicks": 142,
  "recent_clicks": [
    {
      "id": 1,
      "link_id": 1,
      "clicked_at": "2026-09-21T18:00:00Z",
      "ip_address": "192.168.1.1",
      "user_agent": "Mozilla/5.0...",
      "referrer": "https://google.com/"
    }
  ]
}
```

## Running Tests

We use `pytest` for all unit and integration testing. Run the complete suite inside the running API container:

```bash
docker compose exec api pytest -v
```

## Configuration Reference

Key variables inside `.env`:
- `ENVIRONMENT`: (development | production | test)
- `DATABASE_URL`: Async SQLAlchemy connection string (e.g. `postgresql+asyncpg://...`)
- `REDIS_URL`: Redis connection string (e.g. `redis://...`)
- `SECRET_KEY`: Used for JWT generation. Must be kept secret.
- `RATE_LIMIT_REDIRECT`: Number of redirects permitted per 60 seconds (defaults to 60).
- `CORS_ORIGINS`: Comma separated URLs permitted by the API backend.

## Troubleshooting

- **Redis Error / Rate Limit Fails**: The system is designed to "fail-open". If Redis crashes, requests will bypass rate limiting and hit the database directly to maintain API availability.
- **Migrations Failing**: Ensure PostgreSQL is healthy. You can check the health status via `GET /api/v1/ready`. If the DB is down, it returns a 503 response.

## Future Improvements

- Add Geospatial and Browser aggregation for the Click Analytics endpoints.
- Introduce customizable slug URLs for premium users.
- Add Celery for processing large analytical data dumps in real-time.
