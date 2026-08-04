#!/bin/bash
################################################################################
# Cloud SQL Automated Backup Configuration Script for DomOS
#
# Purpose: Enable and configure automated daily backups for Cloud SQL instance
# Run this ONCE when setting up a new Cloud SQL instance
#
# Prerequisites:
#   - gcloud CLI installed and authenticated
#   - Cloud SQL Admin API enabled
#   - Proper IAM permissions (roles/cloudsql.admin)
################################################################################

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-bionic-region-502615-h8}"
INSTANCE_NAME="${CLOUD_SQL_INSTANCE:-domos-db}"
REGION="${GCP_REGION:-europe-west3}"

# Backup Configuration
BACKUP_START_TIME="03:00"  # UTC time for backup window
RETAINED_BACKUPS=7          # Number of automated backups to retain
TRANSACTION_LOG_DAYS=7      # Days to retain transaction logs (for PITR)
BACKUP_LOCATION="eu"        # Storage location for backups

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}DomOS Cloud SQL Backup Configuration${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Project: ${PROJECT_ID}"
echo -e "Instance: ${INSTANCE_NAME}"
echo -e "Region: ${REGION}"
echo -e "${BLUE}========================================${NC}"
echo -e "${YELLOW}Configuration:${NC}"
echo -e "  Backup Start Time: ${BACKUP_START_TIME} UTC"
echo -e "  Retained Backups: ${RETAINED_BACKUPS} days"
echo -e "  Transaction Logs: ${TRANSACTION_LOG_DAYS} days"
echo -e "  Backup Location: ${BACKUP_LOCATION}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check gcloud authentication
echo -e "${YELLOW}[1/5] Checking gcloud authentication...${NC}"
if ! gcloud auth print-identity-token > /dev/null 2>&1; then
    echo -e "${RED}Error: Not authenticated with gcloud. Run 'gcloud auth login'${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Authenticated${NC}"

# Set project
echo -e "${YELLOW}[2/5] Setting project...${NC}"
gcloud config set project "${PROJECT_ID}" --quiet
echo -e "${GREEN}✓ Project set to ${PROJECT_ID}${NC}"

# Get current backup configuration
echo -e "${YELLOW}[3/5] Checking current backup configuration...${NC}"
CURRENT_CONFIG=$(gcloud sql instances describe "${INSTANCE_NAME}" \
    --format="yaml(settings.backupConfiguration)" 2>/dev/null || echo "NOT_FOUND")

if [ "${CURRENT_CONFIG}" == "NOT_FOUND" ]; then
    echo -e "${RED}Error: Instance ${INSTANCE_NAME} not found${NC}"
    exit 1
fi

echo "Current configuration:"
echo "${CURRENT_CONFIG}"
echo ""

# Confirm changes
echo -e "${YELLOW}[4/5] Ready to apply new configuration${NC}"
read -p "Continue? (y/n): " CONFIRM

if [ "${CONFIRM}" != "y" ] && [ "${CONFIRM}" != "Y" ]; then
    echo "Configuration cancelled."
    exit 0
fi

# Apply backup configuration
echo -e "${YELLOW}[5/5] Applying backup configuration...${NC}"
echo "This may take a few minutes..."

gcloud sql instances patch "${INSTANCE_NAME}" \
    --backup-start-time="${BACKUP_START_TIME}" \
    --enable-bin-log \
    --retained-backups-count="${RETAINED_BACKUPS}" \
    --retained-transaction-log-days="${TRANSACTION_LOG_DAYS}" \
    --quiet

if [ $? -eq 0 ]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✓ Backup configuration applied!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    
    # Verify new configuration
    echo "New configuration:"
    gcloud sql instances describe "${INSTANCE_NAME}" \
        --format="yaml(settings.backupConfiguration)"
    
    echo ""
    echo -e "${GREEN}Automated backups are now enabled!${NC}"
    echo ""
    echo "What happens now:"
    echo "  - Daily backups at ${BACKUP_START_TIME} UTC"
    echo "  - ${RETAINED_BACKUPS} most recent backups retained"
    echo "  - Point-in-time recovery available for last ${TRANSACTION_LOG_DAYS} days"
    echo ""
    echo "View backups at:"
    echo "  https://console.cloud.google.com/sql/instances/${INSTANCE_NAME}/backups?project=${PROJECT_ID}"
else
    echo -e "${RED}Error applying backup configuration${NC}"
    exit 1
fi
