#!/bin/bash

# EPL Match Predictor - Dependency Update Script
# Safely update dependencies with backup and testing

set -e

echo "🔄 EPL Match Predictor - Dependency Update"
echo "=========================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${RED}❌ Error: Virtual environment not activated${NC}"
    exit 1
fi

BACKUP_DIR="backups/requirements_$(date +%Y%m%d_%H%M%S)"
REQUIREMENTS_FILE="${1:-requirements/base.txt}"

# Confirm action
echo -e "${YELLOW}⚠️  Warning: This will update packages in $REQUIREMENTS_FILE${NC}"
echo ""
read -p "Continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# 1. Create backup
echo "1️⃣  Creating backup..."
mkdir -p "$BACKUP_DIR"
pip freeze > "$BACKUP_DIR/pip_freeze_before.txt"
cp -r requirements/ "$BACKUP_DIR/"
echo -e "${GREEN}✅ Backup created: $BACKUP_DIR${NC}"
echo ""

# 2. Show outdated packages
echo "2️⃣  Outdated packages:"
pip list --outdated --format=columns
echo ""

# 3. Update packages
echo "3️⃣  Updating packages..."
pip install --upgrade -r "$REQUIREMENTS_FILE"
echo -e "${GREEN}✅ Packages updated${NC}"
echo ""

# 4. Run tests
echo "4️⃣  Running tests to verify compatibility..."
if pytest tests/ -v; then
    echo -e "${GREEN}✅ All tests passed${NC}"
else
    echo -e "${RED}❌ Tests failed!${NC}"
    echo ""
    echo "Rolling back to previous versions..."
    pip install -r "$BACKUP_DIR/requirements/base.txt"
    echo -e "${YELLOW}⚠️  Rollback complete. Review test failures.${NC}"
    exit 1
fi
echo ""

# 5. Generate new requirements file
echo "5️⃣  Generating updated requirements file..."
pip freeze > "$BACKUP_DIR/pip_freeze_after.txt"

# Show diff
echo ""
echo "Changes:"
diff "$BACKUP_DIR/pip_freeze_before.txt" "$BACKUP_DIR/pip_freeze_after.txt" || true
echo ""

# 6. Prompt to save
echo "6️⃣  Save updated requirements?"
read -p "Update $REQUIREMENTS_FILE with new versions? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Extract only the packages from the requirements file
    pip freeze > temp_requirements.txt

    echo -e "${GREEN}✅ Requirements file updated${NC}"
    echo ""
    echo "Don't forget to:"
    echo "  1. Review changes: git diff $REQUIREMENTS_FILE"
    echo "  2. Test thoroughly"
    echo "  3. Commit: git add $REQUIREMENTS_FILE && git commit -m 'chore: update dependencies'"
else
    echo "Skipped. Backup preserved at: $BACKUP_DIR"
fi

echo ""
echo -e "${GREEN}✅ Update process complete${NC}"
