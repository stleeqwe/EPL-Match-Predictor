"""
Production Configuration
========================

Environment-based configuration with security best practices
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field, PostgresDsn, RedisDsn, validator


class Settings(BaseSettings):
    """Production settings with validation"""

    # Application
    APP_NAME: str = "Football Predictor API"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="production", env="ENVIRONMENT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    SECRET_KEY: str = Field(..., env="SECRET_KEY")  # Required

    # Database
    DATABASE_URL: PostgresDsn = Field(..., env="DATABASE_URL")
    DB_POOL_SIZE: int = Field(default=20, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(default=40, env="DB_MAX_OVERFLOW")
    DB_POOL_TIMEOUT: int = Field(default=30, env="DB_POOL_TIMEOUT")

    # Redis
    REDIS_URL: RedisDsn = Field(..., env="REDIS_URL")
    REDIS_CACHE_TTL: int = Field(default=3600, env="REDIS_CACHE_TTL")  # 1 hour

    # API
    API_PREFIX: str = "/api/v1"
    API_RATE_LIMIT: str = Field(default="100/minute", env="API_RATE_LIMIT")
    CORS_ORIGINS: list = Field(
        default=["https://yourdomain.com"],
        env="CORS_ORIGINS"
    )

    # Model
    MODEL_CACHE_DIR: Path = Field(
        default=Path("/app/model_cache"),
        env="MODEL_CACHE_DIR"
    )
    MODEL_VERSION: str = Field(default="1.0", env="MODEL_VERSION")
    BAYESIAN_SAMPLES: int = Field(default=2000, env="BAYESIAN_SAMPLES")
    BAYESIAN_BURNIN: int = Field(default=1000, env="BAYESIAN_BURNIN")
    PREDICTION_CACHE_TTL: int = Field(default=1800, env="PREDICTION_CACHE_TTL")  # 30min

    # Data Collection
    FBREF_RATE_LIMIT: float = Field(default=3.0, env="FBREF_RATE_LIMIT")  # seconds
    UNDERSTAT_RATE_LIMIT: float = Field(default=5.0, env="UNDERSTAT_RATE_LIMIT")
    DATA_COLLECTION_SCHEDULE: str = Field(
        default="0 2 * * *",  # Daily at 2AM UTC
        env="DATA_COLLECTION_SCHEDULE"
    )

    # Monitoring
    PROMETHEUS_PORT: int = Field(default=9090, env="PROMETHEUS_PORT")
    SENTRY_DSN: Optional[str] = Field(default=None, env="SENTRY_DSN")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")

    # Security
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = Field(default=24, env="JWT_EXPIRATION_HOURS")
    BCRYPT_ROUNDS: int = 12

    # Performance
    MAX_WORKERS: int = Field(default=4, env="MAX_WORKERS")
    WORKER_TIMEOUT: int = Field(default=30, env="WORKER_TIMEOUT")

    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @validator("MODEL_CACHE_DIR")
    def create_cache_dir(cls, v):
        v.mkdir(parents=True, exist_ok=True)
        return v

    class Config:
        env_file = ".env.production"
        case_sensitive = True


class DevelopmentSettings(Settings):
    """Development overrides"""
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    DATABASE_URL: PostgresDsn = "postgresql://postgres:postgres@localhost:5432/football_dev"
    REDIS_URL: RedisDsn = "redis://localhost:6379/0"
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:3001"]

    class Config:
        env_file = ".env.development"


class TestSettings(Settings):
    """Test environment"""
    ENVIRONMENT: str = "test"
    DEBUG: bool = True
    DATABASE_URL: PostgresDsn = "postgresql://postgres:postgres@localhost:5432/football_test"
    REDIS_URL: RedisDsn = "redis://localhost:6379/1"

    class Config:
        env_file = ".env.test"


def get_settings() -> Settings:
    """Get settings based on environment"""
    env = os.getenv("ENVIRONMENT", "development")

    if env == "production":
        return Settings()
    elif env == "test":
        return TestSettings()
    else:
        return DevelopmentSettings()


# Global settings instance
settings = get_settings()
