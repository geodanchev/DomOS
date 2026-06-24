#!/bin/bash
# DomOS Cashier MVP - Production Deployment Script
# Usage: ./deploy-prod.sh [--skip-backup] [--skip-build] [--force]
# Deploys the application to production with safety checks

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Parse command line arguments
SKIP_BACKUP=false
SKIP_BUILD=false
FORCE=false

for arg in "$@"; do
    case $arg in
        --skip-backup)
            SKIP_BACKUP=true
            shift
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --force|-f)
            FORCE=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [--skip-backup] [--skip-build] [--force]"
            echo ""
            echo "Options:"
            echo "  --skip-backup   Skip database backup before deployment"
            echo "  --skip-build    Skip Docker image rebuild (use existing images)"
            echo "  --force, -f     Skip confirmation prompts"
            echo "  --help, -h      Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown argument: $arg${NC}"
            echo "Usage: $0 [--skip-backup] [--skip-build] [--force]"
            exit 1
            ;;
    esac
done

echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}   🚀 DomOS Production Deployment${NC}"
echo -e "${CYAN}════════════════════════════════════════════════════════════${NC}"
echo ""

# =============================================================================
# PRE-FLIGHT CHECKS
# =============================================================================

echo -e "${BLUE}📋 Running pre-flight checks...${NC}"
echo ""

# Check 1: Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi
echo -e "${GREEN}  ✓ Docker is running${NC}"

# Check 2: Docker Compose is available
if ! docker compose version > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker Compose is not available.${NC}"
    exit 1
fi
echo -e "${GREEN}  ✓ Docker Compose is available${NC}"

# Check 3: Production compose file exists
if [ ! -f "docker-compose.prod.yml" ]; then
    echo -e "${RED}❌ docker-compose.prod.yml not found${NC}"
    exit 1
fi
echo -e "${GREEN}  ✓ docker-compose.prod.yml exists${NC}"

# Check 4: Environment file exists
if [ ! -f ".env.production" ]; then
    echo -e "${RED}❌ .env.production file not found${NC}"
    echo -e "${YELLOW}  Create it from template: cp .env.production.example .env.production${NC}"
    exit 1
fi
echo -e "${GREEN}  ✓ .env.production exists${NC}"

# Check 5: Load and validate environment variables
set -a
source .env.production
set +a

# Validate required variables
REQUIRED_VARS=("POSTGRES_PASSWORD" "SECRET_KEY" "DOMAIN")
MISSING_VARS=()

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    echo -e "${RED}❌ Missing required environment variables in .env.production:${NC}"
    for var in "${MISSING_VARS[@]}"; do
        echo -e "${RED}     - $var${NC}"
    done
    exit 1
fi
echo -e "${GREEN}  ✓ Required environment variables set${NC}"

# Check 6: SECRET_KEY length
if [ ${#SECRET_KEY} -lt 32 ]; then
    echo -e "${YELLOW}  ⚠ WARNING: SECRET_KEY is shorter than 32 characters${NC}"
    echo -e "${YELLOW}    Generate a secure key: openssl rand -hex 32${NC}"
    if [ "$FORCE" != true ]; then
        read -p "Continue anyway? [y/N]: " CONTINUE
        if [[ ! "$CONTINUE" =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}Deployment cancelled.${NC}"
            exit 0
        fi
    fi
else
    echo -e "${GREEN}  ✓ SECRET_KEY length is adequate${NC}"
fi

# Check 7: POSTGRES_PASSWORD is not default
if [ "$POSTGRES_PASSWORD" = "postgres" ] || [ "$POSTGRES_PASSWORD" = "password" ]; then
    echo -e "${RED}❌ POSTGRES_PASSWORD is set to a default/weak value${NC}"
    echo -e "${RED}   Please set a strong password in .env.production${NC}"
    exit 1
fi
echo -e "${GREEN}  ✓ Database password is not default${NC}"

echo ""
echo -e "${GREEN}✓ All pre-flight checks passed${NC}"

# =============================================================================
# DEPLOYMENT CONFIRMATION
# =============================================================================

if [ "$FORCE" != true ]; then
    echo ""
    echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}   Deployment Configuration${NC}"
    echo -e "${YELLOW}════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${BLUE}  Domain:${NC}          ${DOMAIN:-localhost}"
    echo -e "${BLUE}  Skip Backup:${NC}     $SKIP_BACKUP"
    echo -e "${BLUE}  Skip Build:${NC}      $SKIP_BUILD"
    echo ""
    read -p "Proceed with deployment? [y/N]: " CONFIRM
    
    if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Deployment cancelled.${NC}"
        exit 0
    fi
fi

# =============================================================================
# DATABASE BACKUP (if existing deployment)
# =============================================================================

if [ "$SKIP_BACKUP" != true ]; then
    # Check if database container is running
    if docker ps --format '{{.Names}}' | grep -q "domos-db-prod"; then
        echo ""
        echo -e "${BLUE}💾 Creating database backup before deployment...${NC}"
        
        BACKUP_DIR="./backups"
        mkdir -p "$BACKUP_DIR"
        TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
        BACKUP_FILE="${BACKUP_DIR}/pre_deploy_${TIMESTAMP}.backup"
        
        docker exec domos-db-prod pg_dump -U "${POSTGRES_USER:-postgres}" \
            -d "${POSTGRES_DB:-domos_cashier}" -Fc -f /tmp/backup.dump
        docker cp domos-db-prod:/tmp/backup.dump "$BACKUP_FILE"
        docker exec domos-db-prod rm /tmp/backup.dump
        
        BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        echo -e "${GREEN}  ✓ Backup created: $BACKUP_FILE ($BACKUP_SIZE)${NC}"
    else
        echo ""
        echo -e "${YELLOW}ℹ No existing database container found - skipping backup${NC}"
    fi
else
    echo ""
    echo -e "${YELLOW}⚠ Skipping database backup (--skip-backup flag)${NC}"
fi

# =============================================================================
# BUILD DOCKER IMAGES
# =============================================================================

if [ "$SKIP_BUILD" != true ]; then
    echo ""
    echo -e "${BLUE}🔨 Building Docker images...${NC}"
    
    docker compose -f docker-compose.prod.yml build --no-cache
    
    echo -e "${GREEN}  ✓ Docker images built successfully${NC}"
else
    echo ""
    echo -e "${YELLOW}⚠ Skipping image build (--skip-build flag)${NC}"
fi

# =============================================================================
# STOP EXISTING CONTAINERS
# =============================================================================

echo ""
echo -e "${BLUE}🛑 Stopping existing containers...${NC}"

docker compose -f docker-compose.prod.yml down --remove-orphans 2>/dev/null || true

echo -e "${GREEN}  ✓ Existing containers stopped${NC}"

# =============================================================================
# START PRODUCTION CONTAINERS
# =============================================================================

echo ""
echo -e "${BLUE}🚀 Starting production containers...${NC}"

docker compose -f docker-compose.prod.yml up -d

echo -e "${GREEN}  ✓ Containers started${NC}"

# =============================================================================
# HEALTH CHECKS
# =============================================================================

echo ""
echo -e "${BLUE}🏥 Running health checks...${NC}"

# Wait for database
echo -e "${YELLOW}  ⏳ Waiting for database...${NC}"
MAX_RETRIES=30
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if docker exec domos-db-prod pg_isready -U "${POSTGRES_USER:-postgres}" > /dev/null 2>&1; then
        echo -e "${GREEN}  ✓ Database is ready${NC}"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo -e "${RED}  ❌ Database failed to start${NC}"
        echo -e "${RED}     Check logs: docker logs domos-db-prod${NC}"
        exit 1
    fi
    sleep 2
done

# Wait for backend
echo -e "${YELLOW}  ⏳ Waiting for backend...${NC}"
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    # Check if container is running first
    if ! docker ps --format '{{.Names}}' | grep -q "domos-backend-prod"; then
        RETRY_COUNT=$((RETRY_COUNT + 1))
        sleep 2
        continue
    fi
    
    # Try health endpoint
    if docker exec domos-backend-prod python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" > /dev/null 2>&1; then
        echo -e "${GREEN}  ✓ Backend is healthy${NC}"
        break
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo -e "${YELLOW}  ⚠ Backend health check timed out${NC}"
        echo -e "${YELLOW}    Check logs: docker logs domos-backend-prod${NC}"
    fi
    sleep 2
done

# Wait for frontend
echo -e "${YELLOW}  ⏳ Waiting for frontend...${NC}"
RETRY_COUNT=0
while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if docker ps --format '{{.Names}}' | grep -q "domos-frontend-prod"; then
        if docker exec domos-frontend-prod wget --quiet --tries=1 --spider http://localhost:80/ > /dev/null 2>&1; then
            echo -e "${GREEN}  ✓ Frontend is ready${NC}"
            break
        fi
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo -e "${YELLOW}  ⚠ Frontend health check timed out${NC}"
    fi
    sleep 2
done

# Check Traefik
if docker ps --format '{{.Names}}' | grep -q "domos-traefik"; then
    echo -e "${GREEN}  ✓ Traefik reverse proxy is running${NC}"
else
    echo -e "${YELLOW}  ⚠ Traefik is not running${NC}"
fi

# =============================================================================
# DEPLOYMENT SUMMARY
# =============================================================================

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}   ✅ Production Deployment Complete!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""

# Show running containers
echo -e "${BLUE}Running containers:${NC}"
docker compose -f docker-compose.prod.yml ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo -e "${BLUE}Access URLs:${NC}"
echo "  🌐 Application:  https://${DOMAIN:-localhost}"
echo "  📊 API Docs:     https://${DOMAIN:-localhost}/docs"
echo "  🔧 API Health:   https://${DOMAIN:-localhost}/health"

if [ -n "$TRAEFIK_DASHBOARD_AUTH" ]; then
    echo "  ⚙️  Traefik:      https://traefik.${DOMAIN:-localhost}"
fi

echo ""
echo -e "${BLUE}Useful commands:${NC}"
echo "  📋 View logs:     docker compose -f docker-compose.prod.yml logs -f"
echo "  📋 Backend logs:  docker logs -f domos-backend-prod"
echo "  🔄 Restart:       docker compose -f docker-compose.prod.yml restart"
echo "  🛑 Stop:          docker compose -f docker-compose.prod.yml down"
echo "  💾 Backup DB:     cd backend && ./backup-db.sh"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT: If this is the first deployment:${NC}"
echo "  1. Login with default credentials (admin/admin123)"
echo "  2. IMMEDIATELY change all default passwords"
echo "  3. Configure production-specific settings"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"