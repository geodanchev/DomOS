#!/bin/bash
# ===========================================
# DomOS Cashier - Rate Limit Monitor
# ===========================================
# Monitor rate limit events (HTTP 429) in real-time
# Usage: ./scripts/monitor-ratelimits.sh

set -e

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${YELLOW}==========================================="
echo "DomOS Rate Limit Monitor"
echo -e "===========================================${NC}"
echo ""
echo -e "Monitoring rate limit events (HTTP 429)..."
echo -e "Press ${RED}Ctrl+C${NC} to stop"
echo ""

# Check if jq is available
if ! command -v jq &> /dev/null; then
    echo -e "${RED}Error: jq is required but not installed.${NC}"
    echo "Install with: apt-get install jq"
    exit 1
fi

# Check if container is running
if ! docker ps --format '{{.Names}}' | grep -q 'domos-traefik'; then
    echo -e "${RED}Error: domos-traefik container is not running.${NC}"
    echo "Start the stack with: docker compose -f docker-compose.prod.yml up -d"
    exit 1
fi

# Monitor the access log for 429 responses
docker exec domos-traefik tail -f /var/log/traefik/access.log 2>/dev/null | \
  jq --unbuffered -r 'select(.DownstreamStatus == 429) | 
    "\u001b[31m[429 RATE LIMITED]\u001b[0m \(.StartUTC | split(".")[0])Z | IP: \(.ClientHost) | \(.RequestMethod) \(.RequestPath)"' 2>/dev/null || \
  echo -e "${YELLOW}Note: Log file may be empty. Waiting for rate limit events...${NC}"
