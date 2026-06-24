#!/bin/bash
# DomOS Cashier MVP - Database Setup Script
# Usage: ./setup-db.sh [--with-demo-data] [--fresh]
# Sets up database schema and optionally loads demo data

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse command line arguments
WITH_DEMO_DATA=false
FRESH_INSTALL=false

for arg in "$@"; do
    case $arg in
        --with-demo-data)
            WITH_DEMO_DATA=true
            shift
            ;;
        --fresh)
            FRESH_INSTALL=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown argument: $arg${NC}"
            echo "Usage: $0 [--with-demo-data] [--fresh]"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}   DomOS Database Setup${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker is running${NC}"

# Check if database container exists and is running
if ! docker ps --format '{{.Names}}' | grep -q "^domos-db-dev$"; then
    echo -e "${YELLOW}⚠ Database container is not running${NC}"
    echo -e "${YELLOW}  Starting database container...${NC}"
    docker compose -f docker-compose.dev.yml up -d db
    echo -e "${GREEN}✓ Database container started${NC}"
else
    echo -e "${GREEN}✓ Database container is running${NC}"
fi

# Wait for database to be ready
echo ""
echo -e "${YELLOW}⏳ Waiting for database to be ready...${NC}"
MAX_RETRIES=30
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if docker exec domos-db-dev pg_isready -U postgres -d domos_cashier > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Database is ready${NC}"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo -e "${RED}❌ Database failed to become ready${NC}"
        exit 1
    fi
    sleep 1
done

# Fresh install: drop all tables first
if [ "$FRESH_INSTALL" = true ]; then
    echo ""
    echo -e "${YELLOW}🔄 Fresh install requested - dropping all tables...${NC}"
    docker exec domos-db-dev psql -U postgres -d domos_cashier -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" > /dev/null 2>&1
    echo -e "${GREEN}✓ All tables dropped${NC}"
fi

# Run Alembic migrations
echo ""
echo -e "${YELLOW}📊 Running database migrations...${NC}"
cd backend

# Check if backend container is running, if yes use it, otherwise run locally
if docker ps --format '{{.Names}}' | grep -q "^domos-backend-dev$"; then
    echo -e "${BLUE}  Using backend container for migrations${NC}"
    docker exec domos-backend-dev alembic upgrade head
else
    echo -e "${BLUE}  Running migrations locally${NC}"
    # Activate virtual environment if it exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    alembic upgrade head
fi

echo -e "${GREEN}✓ Database schema updated${NC}"

# Initialize users
echo ""
if [ "$WITH_DEMO_DATA" = true ]; then
    echo -e "${YELLOW}👥 Loading full demo data (users + apartments + obligations)...${NC}"
    if docker ps --format '{{.Names}}' | grep -q "^domos-backend-dev$"; then
        docker exec domos-backend-dev python init_users.py
    else
        python init_users.py
    fi
else
    echo -e "${YELLOW}👥 Creating users only...${NC}"
    if docker ps --format '{{.Names}}' | grep -q "^domos-backend-dev$"; then
        docker exec domos-backend-dev python init_users_only.py
    else
        python init_users_only.py
    fi
fi

cd ..

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Database setup completed successfully!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}Database connection:${NC}"
echo "  Host:     localhost"
echo "  Port:     5432"
echo "  Database: domos_cashier"
echo "  User:     postgres"
echo ""
if [ "$WITH_DEMO_DATA" = true ]; then
    echo -e "${BLUE}Demo data loaded:${NC}"
    echo "  ✓ Users (admin, cecka)"
    echo "  ✓ 20 Apartments with owners"
    echo "  ✓ Monthly obligations"
else
    echo -e "${BLUE}Users created:${NC}"
    echo "  ✓ admin (password: admin123)"
    echo "  ✓ cecka (password: 1234)"
    echo ""
    echo -e "${YELLOW}Note: No apartments or obligations loaded.${NC}"
    echo -e "${YELLOW}      Use --with-demo-data flag to load full demo data.${NC}"
fi
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
