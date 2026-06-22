#!/bin/bash
# DomOS Cashier MVP - Development Stop Script
# Usage: ./stop-dev.sh
# Stops all development services

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🛑 Stopping DomOS Cashier MVP Development Environment..."
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Stop Docker containers
echo "📦 Stopping Docker containers..."
docker compose -f docker-compose.dev.yml down

echo ""
echo -e "${GREEN}✅ All services stopped.${NC}"
echo ""
echo "   To start again, run: ./start-dev.sh"
echo ""
