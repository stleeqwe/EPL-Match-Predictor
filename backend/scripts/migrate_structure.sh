#!/bin/bash

# EPL Match Predictor - Directory Structure Migration
# Phase 1.3: Clean Architecture directory structure

set -e

BACKEND_DIR="backend"
BACKUP_DIR="backups/structure_migration_$(date +%Y%m%d_%H%M%S)"

echo "📦 EPL Match Predictor - Structure Migration to Clean Architecture"
echo "====================================================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. Create backup
echo "1️⃣  Creating backup..."
mkdir -p "$BACKUP_DIR"
echo "  Backing up current backend structure..."
# Only backup if directories exist
for dir in "$BACKEND_DIR"/{ai,api,database,simulation,services}; do
    if [ -d "$dir" ]; then
        cp -r "$dir" "$BACKUP_DIR/" 2>/dev/null || true
    fi
done
echo -e "${GREEN}✅ Backup created at: $BACKUP_DIR${NC}"
echo ""

# 2. Create new directory structure
echo "2️⃣  Creating Clean Architecture directory structure..."

# Core layer
mkdir -p "$BACKEND_DIR/core/domain/entities"
mkdir -p "$BACKEND_DIR/core/domain/value_objects"
mkdir -p "$BACKEND_DIR/core/domain/services"
mkdir -p "$BACKEND_DIR/core/use_cases"
mkdir -p "$BACKEND_DIR/core/ports/repositories"
mkdir -p "$BACKEND_DIR/core/ports/services"

# Infrastructure layer
mkdir -p "$BACKEND_DIR/infrastructure/database/repositories"
mkdir -p "$BACKEND_DIR/infrastructure/database/models"
mkdir -p "$BACKEND_DIR/infrastructure/cache"
mkdir -p "$BACKEND_DIR/infrastructure/external_apis/fpl"
mkdir -p "$BACKEND_DIR/infrastructure/external_apis/odds"
mkdir -p "$BACKEND_DIR/infrastructure/ai_providers"

# API layer
mkdir -p "$BACKEND_DIR/api/v1/endpoints"
mkdir -p "$BACKEND_DIR/api/v1/schemas"
mkdir -p "$BACKEND_DIR/api/v1/dependencies"
mkdir -p "$BACKEND_DIR/api/middleware"

# Shared utilities
mkdir -p "$BACKEND_DIR/shared/exceptions"
mkdir -p "$BACKEND_DIR/shared/logging"
mkdir -p "$BACKEND_DIR/shared/validators"
mkdir -p "$BACKEND_DIR/shared/utils"

# Tests
mkdir -p "$BACKEND_DIR/tests_new/unit/domain"
mkdir -p "$BACKEND_DIR/tests_new/unit/use_cases"
mkdir -p "$BACKEND_DIR/tests_new/integration"
mkdir -p "$BACKEND_DIR/tests_new/e2e"
mkdir -p "$BACKEND_DIR/tests_new/fixtures"

# Alembic migrations
mkdir -p "$BACKEND_DIR/alembic/versions"

# Legacy directory (for old code)
mkdir -p "$BACKEND_DIR/legacy/simulation"
mkdir -p "$BACKEND_DIR/legacy/api"

echo -e "${GREEN}✅ Directory structure created${NC}"
echo ""

# 3. Create __init__.py files
echo "3️⃣  Creating __init__.py files..."
find "$BACKEND_DIR/core" -type d -exec touch {}/__init__.py \; 2>/dev/null || true
find "$BACKEND_DIR/infrastructure" -type d -exec touch {}/__init__.py \; 2>/dev/null || true
find "$BACKEND_DIR/api" -type d -exec touch {}/__init__.py \; 2>/dev/null || true
find "$BACKEND_DIR/shared" -type d -exec touch {}/__init__.py \; 2>/dev/null || true
find "$BACKEND_DIR/tests_new" -type d -exec touch {}/__init__.py \; 2>/dev/null || true
echo -e "${GREEN}✅ __init__.py files created${NC}"
echo ""

# 4. Verification
echo "4️⃣  Verifying structure..."

REQUIRED_DIRS=(
    "core/domain/entities"
    "core/use_cases"
    "infrastructure/database"
    "api/v1/endpoints"
    "tests_new/unit"
    "config"
)

ALL_EXIST=true
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$BACKEND_DIR/$dir" ]; then
        echo -e "${RED}❌ Missing directory: $dir${NC}"
        ALL_EXIST=false
    fi
done

if [ "$ALL_EXIST" = true ]; then
    echo -e "${GREEN}✅ All required directories exist${NC}"
else
    echo -e "${RED}❌ Some directories are missing${NC}"
    exit 1
fi
echo ""

# 5. Generate report
echo "5️⃣  Generating migration report..."

cat > "backend/MIGRATION_REPORT.md" << EOF
# EPL Match Predictor - Clean Architecture Migration Report

**Date:** $(date)
**Backup Location:** $BACKUP_DIR

## New Directory Structure

\`\`\`
backend/
├── core/                          # Core business logic
│   ├── domain/                    # Domain models
│   │   ├── entities/              # Entities
│   │   ├── value_objects/         # Value objects
│   │   └── services/              # Domain services
│   ├── use_cases/                 # Use cases
│   └── ports/                     # Interfaces
│       ├── repositories/
│       └── services/
│
├── infrastructure/                # Infrastructure implementations
│   ├── database/
│   │   ├── repositories/          # Repository implementations
│   │   └── models/                # ORM models
│   ├── cache/                     # Cache implementations
│   ├── external_apis/             # External API clients
│   └── ai_providers/              # AI provider implementations
│
├── api/                           # API layer
│   ├── v1/
│   │   ├── endpoints/             # API endpoints
│   │   ├── schemas/               # Pydantic schemas
│   │   └── dependencies/          # Dependency injection
│   └── middleware/                # Middlewares
│
├── shared/                        # Shared utilities
│   ├── exceptions/                # Custom exceptions
│   ├── logging/                   # Logging configuration
│   ├── validators/                # Validators
│   └── utils/                     # Utility functions
│
├── tests_new/                     # Tests
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── fixtures/
│
├── alembic/                       # Database migrations
│   └── versions/
│
├── config/                        # Configuration
│   ├── settings.py                # ✅ Created
│   └── constants.py               # ✅ Created
│
├── requirements/                  # Dependencies
│   ├── base.txt                   # ✅ Created
│   ├── production.txt             # ✅ Created
│   ├── development.txt            # ✅ Created
│   └── testing.txt                # ✅ Created
│
├── scripts/                       # Utility scripts
│   ├── check_dependencies.sh      # ✅ Created
│   └── update_dependencies.sh     # ✅ Created
│
└── legacy/                        # Legacy code (to be migrated)
    ├── simulation/
    └── api/
\`\`\`

## Migration Status

### Phase 1: Foundation ✅
- [x] Requirements split and versioned
- [x] Centralized configuration (config/settings.py)
- [x] Clean Architecture directory structure
- [ ] Legacy code isolation (Phase 1.4)

### Phase 2: Domain Layer (Pending)
- [ ] Domain entities
- [ ] Value objects
- [ ] Domain services
- [ ] Repository interfaces
- [ ] Use cases

### Phase 3: Infrastructure (Pending)
- [ ] Repository implementations
- [ ] Cache service
- [ ] External API clients
- [ ] AI provider implementations

### Phase 4: API Layer (Pending)
- [ ] API endpoints refactoring
- [ ] Pydantic schemas
- [ ] Dependency injection
- [ ] Middlewares

## Next Steps

1. **Review new structure:**
   \`\`\`bash
   tree -L 3 -d backend/
   \`\`\`

2. **Begin Phase 2: Domain Layer Implementation**
   - Implement domain entities
   - Create value objects
   - Define repository interfaces

3. **Gradually migrate code from legacy/**
   - Move existing code to new structure
   - Update imports
   - Add tests

4. **Update documentation**
   - API documentation
   - Architecture documentation
   - Development guides

## Rollback Instructions

If needed, restore from backup:

\`\`\`bash
# Remove new directories
rm -rf backend/core backend/infrastructure backend/api/v1 backend/shared backend/tests_new

# Restore from backup
cp -r $BACKUP_DIR/* backend/
\`\`\`

---

**Generated:** $(date)
**Script:** migrate_structure.sh
EOF

echo -e "${GREEN}✅ Migration report created: backend/MIGRATION_REPORT.md${NC}"
echo ""

# 6. Display tree structure
if command -v tree &> /dev/null; then
    echo "6️⃣  New directory structure:"
    tree -L 3 -d backend/ -I '__pycache__|*.pyc|venv|node_modules'
else
    echo -e "${YELLOW}⚠️  'tree' command not found. Install with: brew install tree (macOS)${NC}"
fi
echo ""

echo "====================================================================="
echo -e "${GREEN}✅ Migration complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Review: cat backend/MIGRATION_REPORT.md"
echo "  2. Verify: tree -L 3 -d backend/"
echo "  3. Continue: Phase 2 - Domain Layer Implementation"
echo ""
echo "Backup preserved at: $BACKUP_DIR"
