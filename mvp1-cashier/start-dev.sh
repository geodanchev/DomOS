#!/bin/bash
# DomOS Cashier MVP - Development Start Script
# Usage: ./start-dev.sh [--fresh]
# Starts DB + Backend in Docker, Frontend locally with hot reload

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Parse command line arguments
FRESH_INSTALL=false

for arg in "$@"; do
    case $arg in
        --fresh)
            FRESH_INSTALL=true
            shift
            ;;
        *)
            echo -e "${RED}Unknown argument: $arg${NC}"
            echo "Usage: $0 [--fresh]"
            exit 1
            ;;
    esac
done

echo "🚀 Starting DomOS Cashier MVP Development Environment..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Docker is running${NC}"

# Stop any existing frontend container (we'll run it locally)
echo ""
echo "📦 Starting Database and Backend containers..."
docker compose -f docker-compose.dev.yml up -d db backend

# Wait for database to be ready
echo ""
echo "⏳ Waiting for database to be ready..."
MAX_DB_RETRIES=30
DB_RETRY_COUNT=0
while [ $DB_RETRY_COUNT -lt $MAX_DB_RETRIES ]; do
    if docker exec domos-db-dev pg_isready -U postgres -d domos_cashier > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Database is ready${NC}"
        break
    fi
    DB_RETRY_COUNT=$((DB_RETRY_COUNT + 1))
    if [ $DB_RETRY_COUNT -eq $MAX_DB_RETRIES ]; then
        echo -e "${RED}❌ Database failed to become ready${NC}"
        exit 1
    fi
    sleep 1
done

# Check if database is initialized
echo ""
echo "🔍 Checking database initialization..."
TABLE_COUNT=$(docker exec domos-db-dev psql -U postgres -d domos_cashier -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d ' ' || echo "0")

if [ "$FRESH_INSTALL" = true ]; then
    echo -e "${YELLOW}🔄 Fresh install requested - running setup-db.sh --fresh${NC}"
    ./setup-db.sh --fresh
elif [ "$TABLE_COUNT" = "0" ]; then
    echo -e "${YELLOW}⚠ Database not initialized (no tables found)${NC}"
    echo -e "${YELLOW}  Running initial database setup...${NC}"
    ./setup-db.sh
else
    echo -e "${GREEN}✓ Database already initialized ($TABLE_COUNT tables found)${NC}"
fi

# Wait for backend to be healthy
echo ""
echo "⏳ Waiting for backend to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is ready${NC}"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo -e "${YELLOW}⚠ Backend health check timed out, but continuing...${NC}"
    fi
    sleep 1
done

# Navigate to frontend directory
cd frontend

# Check if node_modules exists, if not install dependencies
if [ ! -d "node_modules" ]; then
    echo ""
    echo "📦 Installing frontend dependencies..."
    npm install
fi

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ Development environment is ready!${NC}"
echo ""
echo "   📊 Database:  PostgreSQL on localhost:5432"
echo "   🔧 Backend:   FastAPI on http://localhost:8000"
echo "   🎨 Frontend:  Starting Vite on http://localhost:5173"
echo ""
echo -e "${YELLOW}   Press Ctrl+C to stop the frontend dev server${NC}"
echo -e "${YELLOW}   Run './stop-dev.sh' to stop all services${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""

# Start frontend with hot reload
# Set proxy target to localhost since frontend runs outside Docker
export VITE_PROXY_TARGET=http://localhost:8000
exec npm run dev
