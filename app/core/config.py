from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn, RedisDsn

class Settings(BaseSettings):
    PROJECT_NAME: str = "ShortLink Analytics API"
    ENVIRONMENT: str = "development"
    
    # DB
    DATABASE_URL: PostgresDsn
    
    # Redis
    REDIS_URL: RedisDsn
    
    # Auth
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
