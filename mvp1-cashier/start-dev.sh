#!/bin/bash
# DomOS Cashier MVP - Development Start Script
# Usage: ./start-dev.sh
# Starts DB + Backend in Docker, Frontend locally with hot reload

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

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
