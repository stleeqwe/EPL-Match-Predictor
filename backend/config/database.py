"""
Database Configuration
AI Match Simulation v3.0
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class DatabaseConfig:
    """Database configuration settings"""

    # PostgreSQL
    host: str
    port: int
    database: str
    user: str
    password: str

    # Connection pool settings
    min_connections: int = 2
    max_connections: int = 20

    # Timeouts
    connect_timeout: int = 10
    statement_timeout: int = 30000  # milliseconds

    # SSL
    sslmode: str = 'prefer'

    @property
    def connection_string(self) -> str:
        """Build PostgreSQL connection string"""
        return (
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
            f"?sslmode={self.sslmode}"
        )

    @property
    def connection_params(self) -> dict:
        """Connection parameters as dict"""
        return {
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'user': self.user,
            'password': self.password,
            'connect_timeout': self.connect_timeout,
            'options': f'-c statement_timeout={self.statement_timeout}'
        }


@dataclass
class RedisConfig:
    """Redis configuration settings"""

    host: str
    port: int
    db: int = 0
    password: Optional[str] = None
    decode_responses: bool = True

    # Connection pool
    max_connections: int = 50

    # Timeouts
    socket_timeout: int = 5
    socket_connect_timeout: int = 5

    @property
    def connection_string(self) -> str:
        """Build Redis connection string"""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


def get_database_config() -> DatabaseConfig:
    """Get database config from environment"""
    return DatabaseConfig(
        host=os.getenv('POSTGRES_HOST', 'localhost'),
        port=int(os.getenv('POSTGRES_PORT', '5432')),
        database=os.getenv('POSTGRES_DB', 'soccer_predictor_v3'),
        user=os.getenv('POSTGRES_USER', 'postgres'),
        password=os.getenv('POSTGRES_PASSWORD', ''),
        min_connections=int(os.getenv('DB_MIN_CONNECTIONS', '2')),
        max_connections=int(os.getenv('DB_MAX_CONNECTIONS', '20')),
        sslmode=os.getenv('DB_SSL_MODE', 'prefer')
    )


def get_redis_config() -> RedisConfig:
    """Get Redis config from environment"""
    return RedisConfig(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', '6379')),
        db=int(os.getenv('REDIS_DB', '0')),
        password=os.getenv('REDIS_PASSWORD'),
        max_connections=int(os.getenv('REDIS_MAX_CONNECTIONS', '50'))
    )
