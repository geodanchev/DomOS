#!/bin/bash
# ===========================================
# DomOS Cashier - Rate Limit Daily Report
# ===========================================
# Generate a report of rate limit events
# Usage: ./scripts/ratelimit-report.sh [date]
# Example: ./scripts/ratelimit-report.sh 2026-06-25

set -e

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Date to report on (default: today)
REPORT_DATE=${1:-$(date -u +%Y-%m-%d)}
LOG_FILE="/tmp/traefik_access_$$.log"

echo -e "${BLUE}==========================================="
echo "DomOS Rate Limit Report"
echo -e "===========================================${NC}"
echo -e "Date: ${YELLOW}$REPORT_DATE${NC}"
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
    exit 1
fi

# Copy log from container
echo "Fetching logs from Traefik container..."
docker exec domos-traefik cat /var/log/traefik/access.log > $LOG_FILE 2>/dev/null || true

if [ ! -s $LOG_FILE ]; then
    echo -e "${YELLOW}No log data available.${NC}"
    rm -f $LOG_FILE
    exit 0
fi

# Count total requests for the date
TOTAL_REQUESTS=$(cat $LOG_FILE | jq -r "select(.StartUTC | startswith(\"$REPORT_DATE\"))" 2>/dev/null | wc -l)
RATELIMIT_REQUESTS=$(cat $LOG_FILE | jq -r "select(.DownstreamStatus == 429 and (.StartUTC | startswith(\"$REPORT_DATE\")))" 2>/dev/null | wc -l)

echo ""
echo -e "${GREEN}=== Summary ===${NC}"
echo -e "Total requests: ${BLUE}$TOTAL_REQUESTS${NC}"
echo -e "Rate limited (429): ${RED}$RATELIMIT_REQUESTS${NC}"

if [ "$TOTAL_REQUESTS" -gt 0 ]; then
    PERCENTAGE=$(echo "scale=2; $RATELIMIT_REQUESTS * 100 / $TOTAL_REQUESTS" | bc 2>/dev/null || echo "N/A")
    echo -e "Rate limit percentage: ${YELLOW}${PERCENTAGE}%${NC}"
fi

if [ "$RATELIMIT_REQUESTS" -eq 0 ]; then
    echo ""
    echo -e "${GREEN}No rate limit events for this date.${NC}"
    rm -f $LOG_FILE
    exit 0
fi

echo ""
echo -e "${GREEN}=== Top 10 IPs Hitting Rate Limits ===${NC}"
cat $LOG_FILE | jq -r "select(.DownstreamStatus == 429 and (.StartUTC | startswith(\"$REPORT_DATE\"))) | .ClientHost" 2>/dev/null | \
  sort | uniq -c | sort -rn | head -10 | while read count ip; do
    echo -e "  ${RED}$count${NC} requests from ${BLUE}$ip${NC}"
  done

echo ""
echo -e "${GREEN}=== Rate Limited Endpoints ===${NC}"
cat $LOG_FILE | jq -r "select(.DownstreamStatus == 429 and (.StartUTC | startswith(\"$REPORT_DATE\"))) | .RequestPath" 2>/dev/null | \
  sort | uniq -c | sort -rn | while read count path; do
    echo -e "  ${RED}$count${NC} times: ${YELLOW}$path${NC}"
  done

echo ""
echo -e "${GREEN}=== Hourly Distribution ===${NC}"
cat $LOG_FILE | jq -r "select(.DownstreamStatus == 429 and (.StartUTC | startswith(\"$REPORT_DATE\"))) | .StartUTC[:13]" 2>/dev/null | \
  sort | uniq -c | while read count hour; do
    echo -e "  ${BLUE}${hour}:00${NC} - ${RED}$count${NC} events"
  done

echo ""
echo -e "${GREEN}=== Request Methods ===${NC}"
cat $LOG_FILE | jq -r "select(.DownstreamStatus == 429 and (.StartUTC | startswith(\"$REPORT_DATE\"))) | .RequestMethod" 2>/dev/null | \
  sort | uniq -c | sort -rn | while read count method; do
    echo -e "  ${YELLOW}$method${NC}: ${RED}$count${NC}"
  done

# Cleanup
rm -f $LOG_FILE

echo ""
echo -e "${BLUE}===========================================${NC}"
echo "Report generated at $(date)"
