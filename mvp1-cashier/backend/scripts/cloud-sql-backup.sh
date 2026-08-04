#!/bin/bash
################################################################################
# Cloud SQL Manual Backup Script for DomOS
#
# Purpose: Create on-demand backups of Cloud SQL PostgreSQL instance
# Use when: Before major deployments, migrations, or data changes
#
# Prerequisites:
#   - gcloud CLI installed and authenticated
#   - Cloud SQL Admin API enabled
#   - Proper IAM permissions (roles/cloudsql.admin or roles/cloudsql.editor)
################################################################################

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-bionic-region-502615-h8}"
INSTANCE_NAME="${CLOUD_SQL_INSTANCE:-domos-db}"
REGION="${GCP_REGION:-europe-west3}"
BACKUP_DESCRIPTION="${1:-Manual backup via script}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}DomOS Cloud SQL Backup${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "Project: ${PROJECT_ID}"
echo -e "Instance: ${INSTANCE_NAME}"
echo -e "Region: ${REGION}"
echo -e "Description: ${BACKUP_DESCRIPTION}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check gcloud authentication
echo -e "${YELLOW}[1/4] Checking gcloud authentication...${NC}"
if ! gcloud auth print-identity-token > /dev/null 2>&1; then
    echo -e "${RED}Error: Not authenticated with gcloud. Run 'gcloud auth login'${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Authenticated${NC}"

# Set project
echo -e "${YELLOW}[2/4] Setting project...${NC}"
gcloud config set project "${PROJECT_ID}" --quiet
echo -e "${GREEN}✓ Project set to ${PROJECT_ID}${NC}"

# Get current instance status
echo -e "${YELLOW}[3/4] Checking instance status...${NC}"
INSTANCE_STATUS=$(gcloud sql instances describe "${INSTANCE_NAME}" --format="value(state)" 2>/dev/null || echo "NOT_FOUND")

if [ "${INSTANCE_STATUS}" == "NOT_FOUND" ]; then
    echo -e "${RED}Error: Instance ${INSTANCE_NAME} not found in project ${PROJECT_ID}${NC}"
    exit 1
elif [ "${INSTANCE_STATUS}" != "RUNNABLE" ]; then
    echo -e "${RED}Error: Instance is not in RUNNABLE state (current: ${INSTANCE_STATUS})${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Instance is RUNNABLE${NC}"

# Create backup
echo -e "${YELLOW}[4/4] Creating backup...${NC}"
echo "This may take a few minutes..."

BACKUP_RESULT=$(gcloud sql backups create \
    --instance="${INSTANCE_NAME}" \
    --description="${BACKUP_DESCRIPTION}" \
    --async \
    2>&1)

if [ $? -eq 0 ]; then
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}✓ Backup initiated successfully!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "Backup is running in the background."
    echo "Check status with:"
    echo "  gcloud sql backups list --instance=${INSTANCE_NAME}"
    echo ""
    echo "Or view in Cloud Console:"
    echo "  https://console.cloud.google.com/sql/instances/${INSTANCE_NAME}/backups?project=${PROJECT_ID}"
else
    echo -e "${RED}Error creating backup:${NC}"
    echo "${BACKUP_RESULT}"
    exit 1
fi
