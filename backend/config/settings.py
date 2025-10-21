"""
EPL Match Predictor - Centralized Settings Management
Environment-based configuration with validation using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import Literal, Optional, List
from functools import lru_cache
import os


class DatabaseSettings(BaseSettings):
    """Database configuration"""
    url: str = Field(
        default='sqlite:///backend/data/epl_data.db',
        env='DATABASE_URL'
    )
    pool_size: int = Field(default=20, env='DB_POOL_SIZE')
    max_overflow: int = Field(default=10, env='DB_MAX_OVERFLOW')
    pool_recycle: int = Field(default=3600, env='DB_POOL_RECYCLE')
    echo: bool = Field(default=False, env='DB_ECHO')

    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        if not v.startswith(('postgresql://', 'sqlite://')):
            raise ValueError("Invalid database URL. Must start with postgresql:// or sqlite://")
        return v


class RedisSettings(BaseSettings):
    """Redis configuration"""
    url: str = Field(default='redis://localhost:6379/0', env='REDIS_URL')
    password: Optional[str] = Field(default=None, env='REDIS_PASSWORD')
    max_connections: int = Field(default=50, env='REDIS_MAX_CONNECTIONS')
    socket_timeout: int = Field(default=5, env='REDIS_SOCKET_TIMEOUT')
    socket_connect_timeout: int = Field(default=5, env='REDIS_CONNECT_TIMEOUT')


class CacheSettings(BaseSettings):
    """Cache configuration"""
    enabled: bool = Field(default=True, env='CACHE_ENABLED')
    default_ttl: int = Field(default=3600, env='CACHE_DEFAULT_TTL')

    # Entity-specific TTL
    player_rating_ttl: int = Field(default=3600, env='CACHE_PLAYER_RATING_TTL')
    team_lineup_ttl: int = Field(default=43200, env='CACHE_TEAM_LINEUP_TTL')
    match_prediction_ttl: int = Field(default=3600, env='CACHE_MATCH_PREDICTION_TTL')
    fpl_data_ttl: int = Field(default=1800, env='CACHE_FPL_DATA_TTL')
    odds_data_ttl: int = Field(default=600, env='CACHE_ODDS_DATA_TTL')


class AISettings(BaseSettings):
    """AI provider configuration"""
    provider: Literal['gemini', 'claude', 'qwen'] = Field(
        default='gemini',
        env='AI_PROVIDER'
    )

    # Gemini
    gemini_api_key: str = Field(default='', env='GEMINI_API_KEY')
    gemini_model: str = Field(
        default='gemini-2.0-flash-exp',
        env='GEMINI_MODEL'
    )
    gemini_thinking_budget: int = Field(default=8000, env='GEMINI_THINKING_BUDGET')

    # Claude
    claude_api_key: Optional[str] = Field(default=None, env='CLAUDE_API_KEY')
    claude_model: str = Field(
        default='claude-sonnet-4-20250514',
        env='CLAUDE_MODEL'
    )

    # Qwen (Local Ollama)
    qwen_base_url: str = Field(
        default='http://localhost:11434',
        env='QWEN_BASE_URL'
    )
    qwen_model: str = Field(default='qwen2.5:14b', env='QWEN_MODEL')

    # Rate Limiting
    max_requests_per_minute: int = Field(default=60, env='AI_MAX_REQUESTS_PER_MINUTE')
    timeout: int = Field(default=30, env='AI_TIMEOUT')


class APISettings(BaseSettings):
    """API server configuration"""
    host: str = Field(default='0.0.0.0', env='API_HOST')
    port: int = Field(default=5001, env='API_PORT')
    debug: bool = Field(default=False, env='API_DEBUG')
    workers: int = Field(default=4, env='API_WORKERS')

    # CORS
    cors_origins: List[str] = Field(
        default=['http://localhost:3000'],
        env='API_CORS_ORIGINS'
    )

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, env='API_RATE_LIMIT_ENABLED')
    rate_limit_per_minute: int = Field(default=60, env='API_RATE_LIMIT_PER_MINUTE')


class ExternalAPISettings(BaseSettings):
    """External API configuration"""
    # FPL API
    fpl_base_url: str = Field(
        default='https://fantasy.premierleague.com/api',
        env='FPL_BASE_URL'
    )
    fpl_timeout: int = Field(default=10, env='FPL_TIMEOUT')

    # Odds API
    odds_api_key: Optional[str] = Field(default=None, env='ODDS_API_KEY')
    odds_api_url: str = Field(
        default='https://api.the-odds-api.com/v4',
        env='ODDS_API_URL'
    )
    odds_timeout: int = Field(default=10, env='ODDS_TIMEOUT')

    # API Football
    api_football_key: Optional[str] = Field(default=None, env='API_FOOTBALL_KEY')
    api_football_url: str = Field(
        default='https://v3.football.api-sports.io',
        env='API_FOOTBALL_URL'
    )


class FeatureFlags(BaseSettings):
    """Feature toggle configuration"""
    enable_v3_simulation: bool = Field(default=True, env='ENABLE_V3_SIMULATION')
    enable_payment: bool = Field(default=False, env='ENABLE_PAYMENT')
    enable_ai_rating: bool = Field(default=True, env='ENABLE_AI_RATING')
    enable_value_betting: bool = Field(default=True, env='ENABLE_VALUE_BETTING')
    enable_injury_tracking: bool = Field(default=True, env='ENABLE_INJURY_TRACKING')
    enable_enriched_simulation: bool = Field(default=True, env='ENABLE_ENRICHED_SIMULATION')


class LoggingSettings(BaseSettings):
    """Logging configuration"""
    level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR'] = Field(
        default='INFO',
        env='LOG_LEVEL'
    )
    format: str = Field(
        default='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        env='LOG_FORMAT'
    )
    file_path: Optional[str] = Field(default=None, env='LOG_FILE_PATH')
    max_bytes: int = Field(default=10485760, env='LOG_MAX_BYTES')  # 10MB
    backup_count: int = Field(default=5, env='LOG_BACKUP_COUNT')

    # Structured logging
    use_json: bool = Field(default=False, env='LOG_USE_JSON')
    include_trace: bool = Field(default=True, env='LOG_INCLUDE_TRACE')


class Settings(BaseSettings):
    """Global application settings"""
    environment: Literal['development', 'production', 'testing'] = Field(
        default='development',
        env='ENVIRONMENT'
    )

    # Sub-settings
    database: DatabaseSettings = DatabaseSettings()
    redis: RedisSettings = RedisSettings()
    cache: CacheSettings = CacheSettings()
    ai: AISettings = AISettings()
    api: APISettings = APISettings()
    external_api: ExternalAPISettings = ExternalAPISettings()
    features: FeatureFlags = FeatureFlags()
    logging: LoggingSettings = LoggingSettings()

    # Monitoring
    sentry_dsn: Optional[str] = Field(default=None, env='SENTRY_DSN')
    enable_metrics: bool = Field(default=True, env='ENABLE_METRICS')

    # Stripe Payment
    stripe_api_key: Optional[str] = Field(default=None, env='STRIPE_API_KEY')
    stripe_webhook_secret: Optional[str] = Field(default=None, env='STRIPE_WEBHOOK_SECRET')

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
        case_sensitive = False
        extra = 'allow'


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance

    Returns:
        Settings: Global settings singleton
    """
    return Settings()


# Convenience functions
def get_database_url() -> str:
    """Get database URL"""
    return get_settings().database.url


def get_redis_url() -> str:
    """Get Redis URL"""
    return get_settings().redis.url


def is_production() -> bool:
    """Check if running in production environment"""
    return get_settings().environment == 'production'


def is_development() -> bool:
    """Check if running in development environment"""
    return get_settings().environment == 'development'


def is_testing() -> bool:
    """Check if running in testing environment"""
    return get_settings().environment == 'testing'
