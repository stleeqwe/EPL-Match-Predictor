"""
Database Migration Runner
AI Match Simulation v3.0

Usage:
    python -m database.migrate up      # Run all pending migrations
    python -m database.migrate down    # Rollback last migration
    python -m database.migrate status  # Show migration status
"""

import os
import sys
import psycopg2
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MigrationRunner:
    """Database migration manager"""

    def __init__(self):
        self.migrations_dir = Path(__file__).parent / 'migrations'
        self.conn = None

    def connect(self):
        """Connect to database"""
        try:
            self.conn = psycopg2.connect(
                host=os.getenv('POSTGRES_HOST', 'localhost'),
                port=int(os.getenv('POSTGRES_PORT', '5432')),
                database=os.getenv('POSTGRES_DB', 'soccer_predictor_v3'),
                user=os.getenv('POSTGRES_USER', 'postgres'),
                password=os.getenv('POSTGRES_PASSWORD', '')
            )
            logger.info("Connected to database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            sys.exit(1)

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def ensure_migrations_table(self):
        """Create migrations tracking table if not exists"""
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(50) PRIMARY KEY,
                    description TEXT,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.conn.commit()
            logger.info("Migrations table ensured")

    def get_applied_migrations(self):
        """Get list of applied migrations"""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT version FROM schema_migrations
                ORDER BY version
            """)
            return [row[0] for row in cur.fetchall()]

    def get_pending_migrations(self):
        """Get list of pending migrations"""
        applied = set(self.get_applied_migrations())

        all_migrations = []
        for file in sorted(self.migrations_dir.glob('*.sql')):
            version = file.stem.split('_')[0]
            if version not in applied:
                all_migrations.append(file)

        return all_migrations

    def run_migration(self, migration_file: Path):
        """Run a single migration file"""
        logger.info(f"Running migration: {migration_file.name}")

        try:
            with open(migration_file, 'r') as f:
                sql = f.read()

            with self.conn.cursor() as cur:
                # Execute migration
                cur.execute(sql)

            self.conn.commit()
            logger.info(f"✅ Migration {migration_file.name} completed successfully")

        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ Migration {migration_file.name} failed: {e}")
            raise

    def migrate_up(self):
        """Run all pending migrations"""
        self.ensure_migrations_table()
        pending = self.get_pending_migrations()

        if not pending:
            logger.info("✅ No pending migrations")
            return

        logger.info(f"Found {len(pending)} pending migration(s)")

        for migration_file in pending:
            self.run_migration(migration_file)

        logger.info(f"✅ All {len(pending)} migration(s) applied successfully")

    def migrate_down(self):
        """Rollback last migration"""
        logger.warning("Rollback not implemented yet")
        logger.warning("Please create down migration scripts manually")

    def status(self):
        """Show migration status"""
        self.ensure_migrations_table()

        applied = self.get_applied_migrations()
        all_files = sorted(self.migrations_dir.glob('*.sql'))

        print("\n" + "=" * 60)
        print("MIGRATION STATUS")
        print("=" * 60)

        if applied:
            print("\n✅ Applied Migrations:")
            for version in applied:
                print(f"   - {version}")
        else:
            print("\n⚠️  No migrations applied yet")

        pending = self.get_pending_migrations()
        if pending:
            print("\n⏳ Pending Migrations:")
            for file in pending:
                print(f"   - {file.name}")
        else:
            print("\n✅ All migrations up to date")

        print("\n" + "=" * 60 + "\n")


def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2:
        print("Usage: python -m database.migrate <command>")
        print("Commands:")
        print("  up      - Run all pending migrations")
        print("  down    - Rollback last migration")
        print("  status  - Show migration status")
        sys.exit(1)

    command = sys.argv[1]

    runner = MigrationRunner()

    try:
        runner.connect()

        if command == 'up':
            runner.migrate_up()
        elif command == 'down':
            runner.migrate_down()
        elif command == 'status':
            runner.status()
        else:
            logger.error(f"Unknown command: {command}")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)
    finally:
        runner.close()


if __name__ == '__main__':
    main()
