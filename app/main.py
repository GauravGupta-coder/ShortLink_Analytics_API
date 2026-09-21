import logging
from fastapi import FastAPI, Depends, Request, BackgroundTasks
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.core.config import settings
from app.api.routes import api_router
from app.api.dependencies import get_db, get_redis
from app.services.link import LinkService
from app.services.analytics import AnalyticsService
from app.core.exceptions import global_exception_handler, sqlalchemy_exception_handler
from app.core.logging import setup_logging, LoggingMiddleware
from app.core.rate_limit import RateLimiter
from sqlalchemy.exc import SQLAlchemyError
from fastapi.middleware.cors import CORSMiddleware

# Setup basic logging
setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="A high-performance URL shortener and click analytics engine built with FastAPI, PostgreSQL, and Redis.",
    version="1.0.0",
    contact={
        "name": "Developer",
        "url": "https://github.com/developer/shortlink-analytics-api",
    },
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(LoggingMiddleware)

app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)

app.include_router(api_router, prefix="/api/v1")

@app.get("/", include_in_schema=False)
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}"}

@app.get("/{short_code}", include_in_schema=False, dependencies=[Depends(RateLimiter(times=settings.RATE_LIMIT_REDIRECT, seconds=60))])
async def redirect_to_original(
    request: Request,
    short_code: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis)
):
    """
    Redirect to original URL.
    """
    link_service = LinkService(db, redis)
    original_url, link_id = await link_service.resolve_short_code(short_code)

    # Schedule click tracking in background
    analytics_service = AnalyticsService(db, redis)
    
    # Get request metadata safely
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent", "")
    referrer = request.headers.get("referer", "")
    
    background_tasks.add_task(
        analytics_service.record_click,
        link_id=link_id,
        ip_address=ip_address,
        user_agent_str=user_agent,
        referrer=referrer
    )

    return RedirectResponse(url=original_url, status_code=307)
