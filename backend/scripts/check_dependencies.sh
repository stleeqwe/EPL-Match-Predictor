#!/bin/bash

# EPL Match Predictor - Dependency Check Script
# Validates dependencies for security and consistency

set -e

echo "🔍 EPL Match Predictor - Dependency Check"
echo "=========================================="
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${RED}❌ Error: Virtual environment not activated${NC}"
    echo "Please activate your virtual environment first:"
    echo "  source venv/bin/activate"
    exit 1
fi

echo -e "${GREEN}✅ Virtual environment: $VIRTUAL_ENV${NC}"
echo ""

# 1. Check for security vulnerabilities with pip-audit
echo "1️⃣  Checking for security vulnerabilities (pip-audit)..."
if command -v pip-audit &> /dev/null; then
    if pip-audit --requirement requirements/base.txt; then
        echo -e "${GREEN}✅ No security vulnerabilities found (pip-audit)${NC}"
    else
        echo -e "${RED}❌ Security vulnerabilities detected${NC}"
        exit 1
    fi
else
    echo -e "${YELLOW}⚠️  pip-audit not installed, skipping...${NC}"
    echo "   Install with: pip install pip-audit"
fi
echo ""

# 2. Check with safety
echo "2️⃣  Checking for known security issues (safety)..."
if command -v safety &> /dev/null; then
    if safety check --file requirements/base.txt; then
        echo -e "${GREEN}✅ No known security issues (safety)${NC}"
    else
        echo -e "${YELLOW}⚠️  Security issues found, review above${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  safety not installed, skipping...${NC}"
    echo "   Install with: pip install safety"
fi
echo ""

# 3. Check for outdated packages
echo "3️⃣  Checking for outdated packages..."
OUTDATED=$(pip list --outdated --format=columns)
if [ -z "$OUTDATED" ]; then
    echo -e "${GREEN}✅ All packages are up to date${NC}"
else
    echo -e "${YELLOW}⚠️  Outdated packages found:${NC}"
    echo "$OUTDATED"
    echo ""
    echo "   Run './scripts/update_dependencies.sh' to update (with caution)"
fi
echo ""

# 4. Check for conflicting dependencies
echo "4️⃣  Checking for dependency conflicts..."
if pip check; then
    echo -e "${GREEN}✅ No dependency conflicts${NC}"
else
    echo -e "${RED}❌ Dependency conflicts detected${NC}"
    exit 1
fi
echo ""

# 5. Validate requirements files
echo "5️⃣  Validating requirements files..."

REQUIREMENTS_FILES=(
    "requirements/base.txt"
    "requirements/production.txt"
    "requirements/development.txt"
    "requirements/testing.txt"
)

for file in "${REQUIREMENTS_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "   ${GREEN}✅${NC} $file exists"

        # Check for version pinning
        UNPINNED=$(grep -v '^#' "$file" | grep -v '^-r' | grep -v '^$' | grep -v '==' || true)
        if [ -n "$UNPINNED" ]; then
            echo -e "   ${YELLOW}⚠️  Unpinned packages in $file:${NC}"
            echo "$UNPINNED" | sed 's/^/      /'
        fi
    else
        echo -e "   ${RED}❌${NC} $file missing"
    fi
done
echo ""

# 6. Summary
echo "=========================================="
echo -e "${GREEN}✅ Dependency check complete${NC}"
echo ""
echo "Next steps:"
echo "  - Review any warnings above"
echo "  - Update outdated packages if needed"
echo "  - Run tests: pytest tests/"
