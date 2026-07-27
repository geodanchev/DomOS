#!/bin/bash
################################################################################
# Cloud SQL Restore Script for DomOS
#
# Purpose: Restore Cloud SQL from a backup
# Use when: Disaster recovery or rollback to previous state
#
# CAUTION: This will OVERWRITE all current data!
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

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${RED}========================================${NC}"
echo -e "${RED}⚠️  DANGER: Cloud SQL Restore${NC}"
echo -e "${RED}========================================${NC}"
echo -e "${YELLOW}This will OVERWRITE all current data!${NC}"
echo -e "Project: ${PROJECT_ID}"
echo -e "Instance: ${INSTANCE_NAME}"
echo -e "${RED}========================================${NC}"
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

# List available backups
echo -e "${YELLOW}[3/5] Available backups:${NC}"
echo ""
gcloud sql backups list --instance="${INSTANCE_NAME}" --format="table(id,windowStartTime,status,description)" 2>/dev/null || {
    echo -e "${RED}Error: Could not list backups${NC}"
    exit 1
}
echo ""

# Ask for backup ID
read -p "Enter backup ID to restore (or 'q' to quit): " BACKUP_ID

if [ "${BACKUP_ID}" == "q" ]; then
    echo "Restore cancelled."
    exit 0
fi

# Confirm restore
echo ""
echo -e "${RED}========================================${NC}"
echo -e "${RED}⚠️  FINAL WARNING${NC}"
echo -e "${RED}========================================${NC}"
echo -e "You are about to restore backup ${BACKUP_ID}"
echo -e "${RED}ALL CURRENT DATA WILL BE LOST!${NC}"
echo ""
read -p "Type 'RESTORE' to confirm: " CONFIRM

if [ "${CONFIRM}" != "RESTORE" ]; then
    echo "Restore cancelled."
    exit 0
fi

# Restore backup
echo -e "${YELLOW}[4/5] Restoring backup...${NC}"
echo "This may take several minutes..."

gcloud sql backups restore "${BACKUP_ID}" \
    --restore-instance="${INSTANCE_NAME}" \
    --backup-instance="${INSTANCE_NAME}" \
    --quiet

if [ $? -eq 0 ]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✓ Restore initiated successfully!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${YELLOW}[5/5] Waiting for instance to be ready...${NC}"
    
    # Wait for instance to be RUNNABLE
    while true; do
        STATUS=$(gcloud sql instances describe "${INSTANCE_NAME}" --format="value(state)" 2>/dev/null)
        if [ "${STATUS}" == "RUNNABLE" ]; then
            break
        fi
        echo "Instance status: ${STATUS}. Waiting..."
        sleep 10
    done
    
    echo -e "${GREEN}✓ Instance is RUNNABLE${NC}"
    echo ""
    echo "Restore complete. Verify your data and restart application if needed."
else
    echo -e "${RED}Error during restore${NC}"
    exit 1
fi
