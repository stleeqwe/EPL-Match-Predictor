#!/usr/bin/env python3
"""
Initialize Database for AI Match Simulation v3.0

This script:
1. Creates the database (if needed)
2. Runs all migrations
3. Initializes Redis
4. Seeds initial data (optional)

Usage:
    python init_database_v3.py
"""

import os
import sys
import logging
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_env():
    """Load environment variables"""
    from dotenv import load_dotenv

    env_file = Path(__file__).parent / '.env'
    if not env_file.exists():
        logger.warning(f".env file not found. Using .env.v3.example as template")
        logger.warning(f"Please copy .env.v3.example to .env and fill in values")
        env_file = Path(__file__).parent / '.env.v3.example'

    load_dotenv(env_file)
    logger.info(f"Loaded environment from: {env_file}")


def check_postgres():
    """Check PostgreSQL connection"""
    import psycopg2

    try:
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=int(os.getenv('POSTGRES_PORT', '5432')),
            database='postgres',  # Connect to default database first
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD', '')
        )
        conn.close()
        logger.info("✅ PostgreSQL connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ PostgreSQL connection failed: {e}")
        return False


def create_database():
    """Create database if it doesn't exist"""
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

    db_name = os.getenv('POSTGRES_DB', 'soccer_predictor_v3')

    try:
        # Connect to postgres database
        conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=int(os.getenv('POSTGRES_PORT', '5432')),
            database='postgres',
            user=os.getenv('POSTGRES_USER', 'postgres'),
            password=os.getenv('POSTGRES_PASSWORD', '')
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        cur = conn.cursor()

        # Check if database exists
        cur.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
        exists = cur.fetchone()

        if not exists:
            cur.execute(f'CREATE DATABASE {db_name}')
            logger.info(f"✅ Database '{db_name}' created")
        else:
            logger.info(f"ℹ️  Database '{db_name}' already exists")

        cur.close()
        conn.close()

        return True

    except Exception as e:
        logger.error(f"❌ Failed to create database: {e}")
        return False


def run_migrations():
    """Run database migrations"""
    from database.migrate import MigrationRunner

    try:
        runner = MigrationRunner()
        runner.connect()
        runner.migrate_up()
        runner.close()
        logger.info("✅ Migrations completed successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False


def check_redis():
    """Check Redis connection"""
    import redis

    try:
        client = redis.Redis(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', '6379')),
            db=int(os.getenv('REDIS_DB', '0')),
            password=os.getenv('REDIS_PASSWORD') or None
        )
        client.ping()
        logger.info("✅ Redis connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ Redis connection failed: {e}")
        logger.warning(f"   Make sure Redis is running: redis-server")
        return False


def seed_data():
    """Seed initial data (optional)"""
    logger.info("ℹ️  Skipping data seeding (no seed data defined)")
    # TODO: Add seed data if needed
    return True


def main():
    """Main initialization flow"""
    print("\n" + "=" * 70)
    print("AI MATCH SIMULATION V3.0 - DATABASE INITIALIZATION")
    print("=" * 70 + "\n")

    # Step 1: Load environment
    logger.info("Step 1: Loading environment variables...")
    load_env()

    # Step 2: Check PostgreSQL
    logger.info("\nStep 2: Checking PostgreSQL connection...")
    if not check_postgres():
        logger.error("PostgreSQL is not running or not configured correctly")
        logger.error("Please check your .env file and ensure PostgreSQL is running")
        sys.exit(1)

    # Step 3: Create database
    logger.info("\nStep 3: Creating database...")
    if not create_database():
        sys.exit(1)

    # Step 4: Run migrations
    logger.info("\nStep 4: Running database migrations...")
    if not run_migrations():
        sys.exit(1)

    # Step 5: Check Redis
    logger.info("\nStep 5: Checking Redis connection...")
    if not check_redis():
        logger.warning("Redis is optional but recommended for caching and rate limiting")

    # Step 6: Seed data
    logger.info("\nStep 6: Seeding initial data...")
    seed_data()

    # Success
    print("\n" + "=" * 70)
    print("✅ DATABASE INITIALIZATION COMPLETE!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Update .env with your API keys (Claude, Stripe, etc.)")
    print("2. Install dependencies: pip install -r requirements_v3.txt")
    print("3. Run the application: python -m api.app")
    print("\n" + "=" * 70 + "\n")


if __name__ == '__main__':
    main()
