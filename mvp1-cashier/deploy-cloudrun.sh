#!/bin/bash
# DomOS Cashier - Manual Cloud Run Deployment Script
# Use this for first deployment or manual deployments
#
# Prerequisites:
# - gcloud CLI installed and authenticated
# - Docker installed
# - Artifact Registry repository created
# - Cloud SQL instance running
# - Secrets created in Secret Manager

set -e

# Configuration
PROJECT_ID="bionic-region-502615-h8"
REGION="europe-west3"
CLOUD_SQL_CONNECTION="bionic-region-502615-h8:europe-west3:domos-db"
ARTIFACT_REGISTRY="${REGION}-docker.pkg.dev/${PROJECT_ID}/domos"
BACKEND_SERVICE="domos-cashier-backend"
FRONTEND_SERVICE="domos-cashier-frontend"
SERVICE_ACCOUNT="domos-backend-sa@${PROJECT_ID}.iam.gserviceaccount.com"

# Get current git commit for tagging
GIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "manual")
TAG="${GIT_SHA}-$(date +%Y%m%d-%H%M%S)"

echo "========================================"
echo "DomOS Cashier - Cloud Run Deployment"
echo "========================================"
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo "Tag: ${TAG}"
echo "========================================"

# Check gcloud authentication
echo "[1/8] Checking gcloud authentication..."
gcloud auth print-identity-token > /dev/null 2>&1 || {
    echo "Error: Not authenticated with gcloud. Run 'gcloud auth login'"
    exit 1
}

# Configure docker for Artifact Registry
echo "[2/8] Configuring Docker for Artifact Registry..."
gcloud auth configure-docker ${REGION}-docker.pkg.dev --quiet

# Build backend image
echo "[3/8] Building backend image..."
cd backend
docker build -t ${ARTIFACT_REGISTRY}/cashier-backend:${TAG} \
    -t ${ARTIFACT_REGISTRY}/cashier-backend:latest \
    -f Dockerfile.cloudrun .
cd ..

# Build frontend image
echo "[4/8] Building frontend image..."
cd frontend
docker build -t ${ARTIFACT_REGISTRY}/cashier-frontend:${TAG} \
    -t ${ARTIFACT_REGISTRY}/cashier-frontend:latest \
    -f Dockerfile.cloudrun \
    --build-arg VITE_API_URL=/api .
cd ..

# Push backend image
echo "[5/8] Pushing backend image..."
docker push ${ARTIFACT_REGISTRY}/cashier-backend:${TAG}
docker push ${ARTIFACT_REGISTRY}/cashier-backend:latest

# Push frontend image
echo "[6/8] Pushing frontend image..."
docker push ${ARTIFACT_REGISTRY}/cashier-frontend:${TAG}
docker push ${ARTIFACT_REGISTRY}/cashier-frontend:latest

# Deploy backend
echo "[7/8] Deploying backend to Cloud Run..."
gcloud run deploy ${BACKEND_SERVICE} \
    --image ${ARTIFACT_REGISTRY}/cashier-backend:${TAG} \
    --region ${REGION} \
    --platform managed \
    --service-account ${SERVICE_ACCOUNT} \
    --add-cloudsql-instances ${CLOUD_SQL_CONNECTION} \
    --set-env-vars "ENVIRONMENT=production,DEBUG=false,INIT_DEMO_DATA=false" \
    --set-secrets "SECRET_KEY=domos-secret-key:latest,DATABASE_URL=domos-database-url:latest" \
    --min-instances 0 \
    --max-instances 10 \
    --memory 512Mi \
    --cpu 1 \
    --timeout 300 \
    --concurrency 80 \
    --port 8080 \
    --no-allow-unauthenticated \
    --project ${PROJECT_ID} \
    --quiet

# Get backend URL for CORS configuration
BACKEND_URL=$(gcloud run services describe ${BACKEND_SERVICE} \
    --region ${REGION} \
    --project ${PROJECT_ID} \
    --format='value(status.url)')

# Deploy frontend
echo "[8/8] Deploying frontend to Cloud Run..."
gcloud run deploy ${FRONTEND_SERVICE} \
    --image ${ARTIFACT_REGISTRY}/cashier-frontend:${TAG} \
    --region ${REGION} \
    --platform managed \
    --min-instances 0 \
    --max-instances 10 \
    --memory 256Mi \
    --cpu 1 \
    --timeout 60 \
    --concurrency 200 \
    --port 8080 \
    --allow-unauthenticated \
    --project ${PROJECT_ID} \
    --quiet

# Get frontend URL
FRONTEND_URL=$(gcloud run services describe ${FRONTEND_SERVICE} \
    --region ${REGION} \
    --project ${PROJECT_ID} \
    --format='value(status.url)')

# Update backend CORS with frontend URL
echo "Updating backend CORS configuration..."
gcloud run services update ${BACKEND_SERVICE} \
    --region ${REGION} \
    --project ${PROJECT_ID} \
    --update-env-vars "CORS_ORIGINS=${FRONTEND_URL}" \
    --quiet

echo ""
echo "========================================"
echo "Deployment Complete!"
echo "========================================"
echo "Backend URL: ${BACKEND_URL}"
echo "Frontend URL: ${FRONTEND_URL}"
echo "Tag: ${TAG}"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Run database migrations if needed"
echo "2. Test the health endpoints:"
echo "   curl ${BACKEND_URL}/health"
echo "3. Access the frontend at: ${FRONTEND_URL}"
echo ""
echo "To view logs:"
echo "   gcloud run services logs read ${BACKEND_SERVICE} --region ${REGION}"
echo "   gcloud run services logs read ${FRONTEND_SERVICE} --region ${REGION}"
