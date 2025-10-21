# Database Migrations

This directory contains Alembic database migrations for the EPL Match Predictor application.

## Overview

We use Alembic for database schema migrations. Alembic allows us to:
- Track database schema changes over time
- Apply migrations incrementally
- Rollback changes if needed
- Auto-generate migrations from SQLAlchemy models

## Directory Structure

```
migrations/
├── env.py              # Migration environment configuration
├── script.py.mako      # Template for new migrations
├── README.md           # This file
└── versions/           # Migration scripts
    └── *.py            # Individual migration files
```

## Common Commands

### Create a new migration

**Auto-generate from model changes:**
```bash
cd backend
alembic revision --autogenerate -m "description of changes"
```

**Create empty migration:**
```bash
cd backend
alembic revision -m "description of changes"
```

### Apply migrations

**Upgrade to latest:**
```bash
cd backend
alembic upgrade head
```

**Upgrade by one version:**
```bash
cd backend
alembic upgrade +1
```

**Upgrade to specific revision:**
```bash
cd backend
alembic upgrade <revision_id>
```

### Rollback migrations

**Downgrade by one version:**
```bash
cd backend
alembic downgrade -1
```

**Downgrade to specific revision:**
```bash
cd backend
alembic downgrade <revision_id>
```

**Downgrade to base (remove all migrations):**
```bash
cd backend
alembic downgrade base
```

### Check migration status

**Show current revision:**
```bash
cd backend
alembic current
```

**Show migration history:**
```bash
cd backend
alembic history
```

**Show pending migrations:**
```bash
cd backend
alembic history --verbose
```

## Best Practices

1. **Always review auto-generated migrations** - Alembic's autogenerate is helpful but not perfect
2. **Test migrations both up and down** - Ensure downgrades work correctly
3. **One logical change per migration** - Keep migrations focused and atomic
4. **Add comments** - Explain complex migrations in the docstring
5. **Don't modify old migrations** - Create new migrations instead
6. **Version control** - Always commit migrations to git
7. **Backup before production** - Always backup production database before applying migrations

## Migration Workflow

1. **Make model changes** - Update SQLAlchemy models in `backend/core/domain/entities/`
2. **Generate migration** - Run `alembic revision --autogenerate -m "description"`
3. **Review migration** - Check the generated file in `migrations/versions/`
4. **Test migration** - Apply with `alembic upgrade head` and test
5. **Test rollback** - Downgrade with `alembic downgrade -1` and verify
6. **Commit** - Add to git and commit

## Configuration

Database connection is configured via `backend/config/settings.py`:
- The migration environment reads settings from centralized configuration
- Different environments (dev/prod/test) can have different database URLs
- Set `DATABASE_URL` environment variable to override

## Troubleshooting

### Migration conflicts
If you have migration conflicts (multiple heads):
```bash
alembic merge heads -m "merge migrations"
```

### Reset migrations (development only!)
```bash
# Drop all tables
alembic downgrade base

# Re-apply all migrations
alembic upgrade head
```

### Check database is in sync
```bash
alembic current
alembic history --verbose
```

## Example Migration

```python
"""Add player statistics table

Revision ID: abc123
Revises: xyz789
Create Date: 2024-01-15 10:30:00
"""
from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    """Add player_statistics table"""
    op.create_table(
        'player_statistics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('player_id', sa.Integer(), nullable=False),
        sa.Column('goals', sa.Integer(), default=0),
        sa.Column('assists', sa.Integer(), default=0),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['player_id'], ['players.id'])
    )

def downgrade() -> None:
    """Drop player_statistics table"""
    op.drop_table('player_statistics')
```

## References

- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- Project docs: `docs/architecture/`
