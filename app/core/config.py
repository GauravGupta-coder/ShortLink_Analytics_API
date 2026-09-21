from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, RedisDsn

class Settings(BaseSettings):
    PROJECT_NAME: str = "ShortLink Analytics API"
    ENVIRONMENT: str = "development"
    
    # DB
    DATABASE_URL: PostgresDsn
    POSTGRES_POOL_SIZE: int = 5
    POSTGRES_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: RedisDsn
    
    # Auth
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Security / CORS
    CORS_ORIGINS: list[str] | str = ["*"]

    # Rate Limiting (requests per minute)
    RATE_LIMIT_REGISTER: int = 5
    RATE_LIMIT_LOGIN: int = 5
    RATE_LIMIT_REDIRECT: int = 60

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
