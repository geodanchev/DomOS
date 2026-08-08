#!/bin/bash
# =============================================================================
# Cloud Scheduler Setup for DomOS Monthly Obligations
# =============================================================================
#
# This script creates a Cloud Scheduler job that triggers monthly obligations
# generation on the 1st of each month at 00:05 (Sofia timezone).
#
# Prerequisites:
# - gcloud CLI authenticated with appropriate permissions
# - Cloud Run service deployed
# - Cloud Scheduler API enabled
#
# Usage:
#   ./setup-cloud-scheduler.sh
#
# =============================================================================

set -euo pipefail

# Configuration
PROJECT_ID="bionic-region-502615-h8"
REGION="europe-west3"
SCHEDULER_REGION="europe-west1"  # Cloud Scheduler may have different region availability
BACKEND_SERVICE="domos-cashier-backend"
JOB_NAME="domos-monthly-obligations"
SERVICE_ACCOUNT_NAME="cloud-scheduler-invoker"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Cloud Scheduler Setup for DomOS ===${NC}"
echo

# Step 1: Get Backend URL
echo -e "${YELLOW}Step 1: Getting Backend URL...${NC}"
BACKEND_URL=$(gcloud run services describe "$BACKEND_SERVICE" \
    --project="$PROJECT_ID" \
    --region="$REGION" \
    --format='value(status.url)')

if [ -z "$BACKEND_URL" ]; then
    echo -e "${RED}Error: Could not get backend URL${NC}"
    exit 1
fi

echo "Backend URL: $BACKEND_URL"
TARGET_URL="${BACKEND_URL}/api/cron/generate-monthly-obligations"
echo "Target URL: $TARGET_URL"
echo

# Step 2: Create Service Account (if not exists)
echo -e "${YELLOW}Step 2: Creating Service Account...${NC}"
SA_EMAIL="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

if gcloud iam service-accounts describe "$SA_EMAIL" --project="$PROJECT_ID" &>/dev/null; then
    echo "Service account already exists: $SA_EMAIL"
else
    gcloud iam service-accounts create "$SERVICE_ACCOUNT_NAME" \
        --project="$PROJECT_ID" \
        --display-name="Cloud Scheduler Invoker for DomOS" \
        --description="Service account for Cloud Scheduler to invoke Cloud Run endpoints"
    echo "Created service account: $SA_EMAIL"
fi
echo

# Step 3: Grant Cloud Run Invoker role to Service Account
echo -e "${YELLOW}Step 3: Granting Cloud Run Invoker role...${NC}"
gcloud run services add-iam-policy-binding "$BACKEND_SERVICE" \
    --project="$PROJECT_ID" \
    --region="$REGION" \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/run.invoker" \
    --quiet

echo "Granted roles/run.invoker to $SA_EMAIL"
echo

# Step 4: Enable Cloud Scheduler API (if not enabled)
echo -e "${YELLOW}Step 4: Enabling Cloud Scheduler API...${NC}"
gcloud services enable cloudscheduler.googleapis.com --project="$PROJECT_ID" || true
echo

# Step 5: Create or Update Cloud Scheduler Job
echo -e "${YELLOW}Step 5: Creating Cloud Scheduler Job...${NC}"

# Check if job exists
if gcloud scheduler jobs describe "$JOB_NAME" \
    --project="$PROJECT_ID" \
    --location="$SCHEDULER_REGION" &>/dev/null; then
    echo "Job exists, updating..."
    gcloud scheduler jobs update http "$JOB_NAME" \
        --project="$PROJECT_ID" \
        --location="$SCHEDULER_REGION" \
        --schedule="5 0 1 * *" \
        --time-zone="Europe/Sofia" \
        --uri="$TARGET_URL" \
        --http-method="POST" \
        --oidc-service-account-email="$SA_EMAIL" \
        --oidc-token-audience="$BACKEND_URL" \
        --attempt-deadline="300s" \
        --description="Generates monthly obligations for all apartments on the 1st of each month"
else
    echo "Creating new job..."
    gcloud scheduler jobs create http "$JOB_NAME" \
        --project="$PROJECT_ID" \
        --location="$SCHEDULER_REGION" \
        --schedule="5 0 1 * *" \
        --time-zone="Europe/Sofia" \
        --uri="$TARGET_URL" \
        --http-method="POST" \
        --oidc-service-account-email="$SA_EMAIL" \
        --oidc-token-audience="$BACKEND_URL" \
        --attempt-deadline="300s" \
        --description="Generates monthly obligations for all apartments on the 1st of each month"
fi

echo
echo -e "${GREEN}=== Setup Complete ===${NC}"
echo
echo "Summary:"
echo "  Job Name: $JOB_NAME"
echo "  Schedule: 5 0 1 * * (00:05 on 1st of each month, Sofia time)"
echo "  Target: $TARGET_URL"
echo "  Service Account: $SA_EMAIL"
echo
echo "To test the job manually:"
echo "  gcloud scheduler jobs run $JOB_NAME --project=$PROJECT_ID --location=$SCHEDULER_REGION"
echo
echo "To view job logs:"
echo "  gcloud logging read 'resource.type=cloud_scheduler_job AND resource.labels.job_id=$JOB_NAME' --project=$PROJECT_ID --limit=10"
