"""
Database Connection Pool
AI Match Simulation v3.0
"""

import psycopg2
from psycopg2 import pool, Error
from psycopg2.extras import RealDictCursor
import redis
from contextlib import contextmanager
from typing import Generator, Optional
import logging

from config.database import get_database_config, get_redis_config

logger = logging.getLogger(__name__)


class DatabasePool:
    """PostgreSQL connection pool manager"""

    _instance: Optional['DatabasePool'] = None
    _pool: Optional[pool.ThreadedConnectionPool] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(self):
        """Initialize connection pool"""
        if self._pool is not None:
            logger.warning("Connection pool already initialized")
            return

        try:
            config = get_database_config()

            self._pool = pool.ThreadedConnectionPool(
                minconn=config.min_connections,
                maxconn=config.max_connections,
                **config.connection_params
            )

            logger.info(
                f"PostgreSQL connection pool initialized: "
                f"{config.min_connections}-{config.max_connections} connections"
            )

        except Error as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise

    def close(self):
        """Close all connections in pool"""
        if self._pool:
            self._pool.closeall()
            self._pool = None
            logger.info("PostgreSQL connection pool closed")

    @contextmanager
    def get_connection(
        self,
        cursor_factory=RealDictCursor
    ) -> Generator:
        """
        Get database connection from pool

        Usage:
            with db_pool.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM users")
        """
        if self._pool is None:
            raise RuntimeError("Connection pool not initialized")

        conn = None
        try:
            conn = self._pool.getconn()
            conn.cursor_factory = cursor_factory
            yield conn
            conn.commit()

        except Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise

        finally:
            if conn:
                self._pool.putconn(conn)

    @contextmanager
    def get_cursor(
        self,
        cursor_factory=RealDictCursor
    ) -> Generator:
        """
        Get database cursor (convenience method)

        Usage:
            with db_pool.get_cursor() as cur:
                cur.execute("SELECT * FROM users")
                results = cur.fetchall()
        """
        with self.get_connection(cursor_factory) as conn:
            with conn.cursor() as cur:
                yield cur


class RedisPool:
    """Redis connection pool manager"""

    _instance: Optional['RedisPool'] = None
    _client: Optional[redis.Redis] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(self):
        """Initialize Redis connection pool"""
        if self._client is not None:
            logger.warning("Redis client already initialized")
            return

        try:
            config = get_redis_config()

            self._client = redis.Redis(
                host=config.host,
                port=config.port,
                db=config.db,
                password=config.password,
                decode_responses=config.decode_responses,
                socket_timeout=config.socket_timeout,
                socket_connect_timeout=config.socket_connect_timeout,
                max_connections=config.max_connections
            )

            # Test connection
            self._client.ping()

            logger.info(
                f"Redis connection pool initialized: "
                f"{config.host}:{config.port}/{config.db}"
            )

        except redis.RedisError as e:
            logger.error(f"Failed to initialize Redis: {e}")
            raise

    def close(self):
        """Close Redis connection"""
        if self._client:
            self._client.close()
            self._client = None
            logger.info("Redis connection closed")

    @property
    def client(self) -> redis.Redis:
        """Get Redis client"""
        if self._client is None:
            raise RuntimeError("Redis client not initialized")
        return self._client


# Global instances
db_pool = DatabasePool()
redis_pool = RedisPool()


def init_databases():
    """Initialize all database connections"""
    logger.info("Initializing database connections...")
    db_pool.initialize()
    redis_pool.initialize()
    logger.info("Database connections initialized successfully")


def close_databases():
    """Close all database connections"""
    logger.info("Closing database connections...")
    db_pool.close()
    redis_pool.close()
    logger.info("Database connections closed successfully")


# Convenience function for getting connection
def get_db():
    """Get database connection (for use in Flask app context)"""
    return db_pool.get_connection()


def get_redis():
    """Get Redis client"""
    return redis_pool.client


def get_connection():
    """
    Get a simple PostgreSQL connection for testing.

    Returns a psycopg2 connection object.
    """
    config = get_database_config()
    return psycopg2.connect(**config.connection_params)
