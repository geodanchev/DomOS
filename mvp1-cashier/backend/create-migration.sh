#!/bin/bash

################################################################################
# Create Migration Helper for DomOS Cashier
# 
# Purpose: Simplify creation of new Alembic migrations
# Usage: ./create-migration.sh "migration_description"
################################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "========================================"
echo "DomOS Migration Helper"
echo "========================================"
echo ""

# Check if migration description provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: Migration description required${NC}"
    echo ""
    echo "Usage:"
    echo "  ./create-migration.sh \"migration_description\""
    echo ""
    echo "Examples:"
    echo "  ./create-migration.sh \"add user roles\""
    echo "  ./create-migration.sh \"create receipts table\""
    echo "  ./create-migration.sh \"add payment void column\""
    echo ""
    exit 1
fi

MIGRATION_MSG="$1"

# Validate migration message
if [[ ! "$MIGRATION_MSG" =~ ^[a-zA-Z0-9\ _-]+$ ]]; then
    echo -e "${RED}Error: Migration description contains invalid characters${NC}"
    echo "Use only: letters, numbers, spaces, hyphens, underscores"
    exit 1
fi

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Check if alembic is available
if ! command -v alembic &> /dev/null; then
    echo -e "${RED}Error: Alembic not found${NC}"
    echo "Install with: pip install alembic"
    exit 1
fi

# Check if models are importable
echo -e "${BLUE}Checking model imports...${NC}"
if ! python -c "from app.models import *" 2>/dev/null; then
    echo -e "${RED}Error: Cannot import models${NC}"
    echo "Make sure all models are properly defined and importable"
    exit 1
fi
echo -e "${GREEN}✓ Models OK${NC}"
echo ""

# Show current migration state
echo -e "${BLUE}Current migration state:${NC}"
alembic current
echo ""

# Create backup before generating migration
echo -e "${YELLOW}Creating safety backup before migration...${NC}"
if [ -f ./backup-db.sh ]; then
    ./backup-db.sh > /dev/null 2>&1 || true
    echo -e "${GREEN}✓ Backup created${NC}"
else
    echo -e "${YELLOW}⚠ Backup script not found, skipping backup${NC}"
fi
echo ""

# Generate migration
echo -e "${BLUE}Generating migration: ${MIGRATION_MSG}${NC}"
echo ""

alembic revision --autogenerate -m "$MIGRATION_MSG"

echo ""
echo "========================================"
echo -e "${GREEN}Migration created successfully!${NC}"
echo "========================================"
echo ""

# Find the newly created migration file
LATEST_MIGRATION=$(ls -t alembic/versions/*.py | head -n 1)

if [ -n "$LATEST_MIGRATION" ]; then
    echo -e "${BLUE}Migration file:${NC} $LATEST_MIGRATION"
    echo ""
    
    # Show migration content preview
    echo -e "${BLUE}Migration preview:${NC}"
    echo "-----------------------------------"
    head -n 30 "$LATEST_MIGRATION"
    echo "..."
    echo "-----------------------------------"
    echo ""
fi

# Show next steps
echo -e "${YELLOW}Next steps:${NC}"
echo ""
echo "1. Review the migration file:"
echo "   ${LATEST_MIGRATION}"
echo ""
echo "2. Edit if needed (add custom logic, data migrations, etc.)"
echo ""
echo "3. Apply the migration:"
echo -e "   ${GREEN}alembic upgrade head${NC}"
echo ""
echo "4. Or test with dry-run first:"
echo -e "   ${GREEN}alembic upgrade head --sql${NC}"
echo ""
echo "5. If something goes wrong, rollback:"
echo -e "   ${GREEN}alembic downgrade -1${NC}"
echo ""

# Offer to show migration history
read -p "Show migration history? [y/N]: " SHOW_HISTORY

if [[ "$SHOW_HISTORY" =~ ^[Yy]$ ]]; then
    echo ""
    echo "========================================"
    echo "Migration History"
    echo "========================================"
    alembic history --verbose
fi

echo ""
echo -e "${GREEN}Done!${NC}"
