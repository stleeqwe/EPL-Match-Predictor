"""
Configuration validation and management
"""
import os
from typing import Optional


class Config:
    """Application configuration"""

    # Flask
    FLASK_APP = os.getenv('FLASK_APP', 'api/app.py')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', '1') == '1'

    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///epl_predictions.db')

    # API
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', '5001'))

    # Cache
    CACHE_TYPE = os.getenv('CACHE_TYPE', 'simple')
    CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_DEFAULT_TIMEOUT', '300'))

    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000')

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    @classmethod
    def validate(cls) -> bool:
        """
        Validate required environment variables

        Returns:
            bool: True if all required variables are set

        Raises:
            ValueError: If required variables are missing
        """
        required_vars = []
        missing_vars = []

        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}\n"
                f"Please check .env.example for required configuration."
            )

        return True

    @classmethod
    def get_database_path(cls) -> str:
        """Get database file path from DATABASE_URL"""
        db_url = cls.DATABASE_URL
        if db_url.startswith('sqlite:///'):
            return db_url.replace('sqlite:///', '')
        return db_url


# Validate configuration on import (only in production)
if os.getenv('FLASK_ENV') == 'production':
    Config.validate()
