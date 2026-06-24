#!/bin/bash
# DomOS Cashier MVP - Database Reset Script
# Usage: ./reset-db.sh [--force] [--with-demo-data]
# WARNING: This will DELETE ALL DATA and recreate the database!

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
FORCE=false
WITH_DEMO_DATA=false

for arg in "$@"; do
    case $arg in
        --force|-f)
            FORCE=true
            shift
            ;;
        --with-demo-data)
            WITH_DEMO_DATA=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--force] [--with-demo-data]"
            echo ""
            echo "Options:"
            echo "  --force, -f       Skip confirmation prompt"
            echo "  --with-demo-data  Load demo data after reset (apartments, obligations, payments)"
            echo "  --help, -h        Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown argument: $arg${NC}"
            echo "Usage: $0 [--force] [--with-demo-data]"
            exit 1
            ;;
    esac
done

echo -e "${RED}════════════════════════════════════════════════════════════${NC}"
echo -e "${RED}   ⚠️  DATABASE RESET - ALL DATA WILL BE DELETED!${NC}"
echo -e "${RED}════════════════════════════════════════════════════════════${NC}"
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
    sleep 3
    echo -e "${GREEN}✓ Database container started${NC}"
else
    echo -e "${GREEN}✓ Database container is running${NC}"
fi

# Confirmation prompt
if [ "$FORCE" != true ]; then
    echo ""
    echo -e "${YELLOW}This will:${NC}"
    echo "  1. Drop ALL tables in the database"
    echo "  2. Delete all data (apartments, payments, users, etc.)"
    echo "  3. Recreate empty schema with migrations"
    if [ "$WITH_DEMO_DATA" = true ]; then
        echo "  4. Load demo data (apartments, obligations, payments)"
    else
        echo "  4. Create only basic users (admin, cecka)"
    fi
    echo ""
    echo -e "${RED}THIS ACTION CANNOT BE UNDONE!${NC}"
    echo ""
    read -p "Type 'YES' to confirm: " CONFIRM
    
    if [ "$CONFIRM" != "YES" ]; then
        echo ""
        echo -e "${YELLOW}Reset cancelled.${NC}"
        exit 0
    fi
fi

echo ""
echo -e "${YELLOW}🗑️  Dropping all tables...${NC}"

# Drop all tables using psql
docker exec domos-db-dev psql -U postgres -d domos_cashier -c "
    DROP SCHEMA public CASCADE;
    CREATE SCHEMA public;
    GRANT ALL ON SCHEMA public TO postgres;
    GRANT ALL ON SCHEMA public TO public;
" > /dev/null 2>&1

echo -e "${GREEN}✓ All tables dropped${NC}"

# Run migrations
echo ""
echo -e "${YELLOW}📊 Running database migrations...${NC}"

if docker ps --format '{{.Names}}' | grep -q "^domos-backend-dev$"; then
    echo -e "${BLUE}  Using backend container for migrations${NC}"
    docker exec domos-backend-dev alembic upgrade head
else
    echo -e "${BLUE}  Running migrations locally${NC}"
    cd backend
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/domos_cashier"
    alembic upgrade head
    cd ..
fi

echo -e "${GREEN}✓ Database schema created${NC}"

# Initialize data
echo ""
if [ "$WITH_DEMO_DATA" = true ]; then
    echo -e "${YELLOW}👥 Loading full demo data...${NC}"
    if docker ps --format '{{.Names}}' | grep -q "^domos-backend-dev$"; then
        docker exec domos-backend-dev python init_db.py
    else
        cd backend
        python init_db.py
        cd ..
    fi
    echo -e "${GREEN}✓ Demo data loaded${NC}"
else
    echo -e "${YELLOW}👥 Creating users only...${NC}"
    if docker ps --format '{{.Names}}' | grep -q "^domos-backend-dev$"; then
        docker exec domos-backend-dev python init_users_only.py
    else
        cd backend
        python init_users_only.py
        cd ..
    fi
    echo -e "${GREEN}✓ Users created${NC}"
fi

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Database reset completed successfully!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${BLUE}Database connection:${NC}"
echo "  Host:     localhost"
echo "  Port:     5432"
echo "  Database: domos_cashier"
echo "  User:     postgres"
echo ""
echo -e "${BLUE}Login credentials:${NC}"
echo "  Admin:   username=admin, password=admin123"
echo "  Cashier: username=cecka, password=1234"
echo ""
if [ "$WITH_DEMO_DATA" = true ]; then
    echo -e "${BLUE}Demo data includes:${NC}"
    echo "  ✓ 10 Apartments with owners"
    echo "  ✓ Monthly obligations"
    echo "  ✓ Sample payments"
else
    echo -e "${YELLOW}Note: No demo data loaded. Use --with-demo-data flag to include it.${NC}"
fi
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
