# DomOS Cashier - Cloud Run Deployment Guide

## Overview

This guide covers deploying DomOS Cashier to Google Cloud Run with Cloud SQL PostgreSQL.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Google Cloud Platform                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐        ┌─────────────────┐                 │
│  │   Cloud Run     │        │   Cloud Run     │                 │
│  │   Frontend      │───────▶│   Backend       │                 │
│  │   (nginx)       │  /api  │   (FastAPI)     │                 │
│  └────────┬────────┘        └────────┬────────┘                 │
│           │                          │                           │
│           │                          │ Unix Socket               │
│           │                          ▼                           │
│           │                 ┌─────────────────┐                 │
│           │                 │   Cloud SQL     │                 │
│           │                 │   PostgreSQL    │                 │
│           │                 └─────────────────┘                 │
│           │                          ▲                           │
│           │                          │                           │
│           │                 ┌─────────────────┐                 │
│           │                 │ Secret Manager  │                 │
│           │                 │ - SECRET_KEY    │                 │
│           │                 │ - DATABASE_URL  │                 │
│           │                 └─────────────────┘                 │
│           │                                                      │
│  ┌────────┴────────┐                                            │
│  │ Artifact        │                                            │
│  │ Registry        │                                            │
│  │ (Docker images) │                                            │
│  └─────────────────┘                                            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

### Infrastructure (already created)

| Resource | Details |
|----------|--------|
| **Project** | `bionic-region-502615-h8` |
| **Region** | `europe-west3` (Frankfurt) |
| **Artifact Registry** | `europe-west3-docker.pkg.dev/bionic-region-502615-h8/domos` |
| **Cloud SQL** | Instance: `domos-db`, Database: `domos`, User: `domos_user` |
| **Cloud SQL Connection** | `bionic-region-502615-h8:europe-west3:domos-db` |
| **Runtime SA** | `domos-backend-sa@bionic-region-502615-h8.iam.gserviceaccount.com` |

### Secrets (in Secret Manager)

| Secret Name | Purpose |
|-------------|--------|
| `domos-secret-key` | Application secret for JWT tokens |
| `domos-database-url` | PostgreSQL connection string |
| `domos-db-password` | Database password (backup) |

## Deployment Methods

### Method 1: Manual Deployment Script

Best for first deployment or when you need full control.

```bash
cd mvp1-cashier
./deploy-cloudrun.sh
```

This script:
1. Builds backend and frontend Docker images
2. Pushes to Artifact Registry
3. Deploys to Cloud Run
4. Configures CORS automatically

### Method 2: Cloud Build CI/CD

Automatic deployment triggered by Git push.

```bash
# Submit build manually
gcloud builds submit \
  --config=cloudbuild.yaml \
  --project=bionic-region-502615-h8

# Or set up trigger for automatic deployment
gcloud builds triggers create github \
  --name="domos-cashier-deploy" \
  --repo-owner="geodanchev" \
  --repo-name="DomOS" \
  --branch-pattern="^main$" \
  --build-config="mvp1-cashier/cloudbuild.yaml" \
  --project=bionic-region-502615-h8
```

### Method 3: Direct gcloud Commands

For individual service updates.

```bash
# Deploy backend only
gcloud run deploy domos-cashier-backend \
  --image europe-west3-docker.pkg.dev/bionic-region-502615-h8/domos/cashier-backend:latest \
  --region europe-west3 \
  --platform managed \
  --project bionic-region-502615-h8

# Deploy frontend only
gcloud run deploy domos-cashier-frontend \
  --image europe-west3-docker.pkg.dev/bionic-region-502615-h8/domos/cashier-frontend:latest \
  --region europe-west3 \
  --platform managed \
  --project bionic-region-502615-h8
```

## Configuration

### Backend Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8080` | Server port (set by Cloud Run) |
| `ENVIRONMENT` | `development` | Environment name |
| `DEBUG` | `true` | Enable debug mode |
| `SECRET_KEY` | - | JWT secret (from Secret Manager) |
| `DATABASE_URL` | - | PostgreSQL URL (from Secret Manager) |
| `CORS_ORIGINS` | - | Allowed CORS origins |
| `INIT_DEMO_DATA` | `true` | Initialize demo data |

### Frontend Build Arguments

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | `/api` | Backend API URL |

## Health Endpoints

| Endpoint | Purpose | Success Response |
|----------|---------|------------------|
| `/health` | Basic health check | `{"status": "healthy"}` |
| `/health/live` | Liveness probe | `{"status": "alive"}` |
| `/health/ready` | Readiness probe | `{"status": "ready", "database": "connected"}` |
| `/health/startup` | Startup probe | `{"status": "started"}` |

## Database Migrations

Run migrations using Cloud Run Jobs:

```bash
# Create migration job
gcloud run jobs create domos-migrations \
  --image europe-west3-docker.pkg.dev/bionic-region-502615-h8/domos/cashier-backend:latest \
  --region europe-west3 \
  --set-cloudsql-instances bionic-region-502615-h8:europe-west3:domos-db \
  --set-secrets DATABASE_URL=domos-database-url:latest \
  --command "alembic" \
  --args "upgrade,head" \
  --project bionic-region-502615-h8

# Execute migrations
gcloud run jobs execute domos-migrations \
  --region europe-west3 \
  --project bionic-region-502615-h8 \
  --wait
```

## Monitoring

### View Logs

```bash
# Backend logs
gcloud run services logs read domos-cashier-backend \
  --region europe-west3 \
  --project bionic-region-502615-h8 \
  --limit 100

# Frontend logs
gcloud run services logs read domos-cashier-frontend \
  --region europe-west3 \
  --project bionic-region-502615-h8 \
  --limit 100

# Tail logs in real-time
gcloud alpha run services logs tail domos-cashier-backend \
  --region europe-west3 \
  --project bionic-region-502615-h8
```

### Service Status

```bash
# List services
gcloud run services list \
  --region europe-west3 \
  --project bionic-region-502615-h8

# Describe service
gcloud run services describe domos-cashier-backend \
  --region europe-west3 \
  --project bionic-region-502615-h8

# List revisions
gcloud run revisions list \
  --service domos-cashier-backend \
  --region europe-west3 \
  --project bionic-region-502615-h8
```

## Troubleshooting

### Common Issues

#### 1. Container fails to start

```bash
# Check logs for startup errors
gcloud run services logs read domos-cashier-backend \
  --region europe-west3 \
  --project bionic-region-502615-h8 \
  --limit 50
```

**Common causes:**
- Missing environment variables
- Secret access denied
- Database connection failed

#### 2. Database connection errors

```bash
# Verify Cloud SQL connection
gcloud sql instances describe domos-db \
  --project bionic-region-502615-h8

# Check service account permissions
gcloud projects get-iam-policy bionic-region-502615-h8 \
  --flatten="bindings[].members" \
  --filter="bindings.members:domos-backend-sa"
```

#### 3. Secret access denied

```bash
# Verify secret exists
gcloud secrets describe domos-secret-key \
  --project bionic-region-502615-h8

# Check service account has access
gcloud secrets get-iam-policy domos-secret-key \
  --project bionic-region-502615-h8
```

#### 4. CORS errors

```bash
# Update CORS origins
gcloud run services update domos-cashier-backend \
  --region europe-west3 \
  --project bionic-region-502615-h8 \
  --update-env-vars "CORS_ORIGINS=https://your-frontend-url.run.app"
```

### Rollback

```bash
# List revisions
gcloud run revisions list \
  --service domos-cashier-backend \
  --region europe-west3 \
  --project bionic-region-502615-h8

# Route traffic to previous revision
gcloud run services update-traffic domos-cashier-backend \
  --region europe-west3 \
  --project bionic-region-502615-h8 \
  --to-revisions=PREVIOUS_REVISION=100
```

## Cost Estimation

| Resource | Estimated Monthly Cost |
|----------|------------------------|
| Cloud SQL (db-f1-micro) | $7-15 |
| Cloud Run (Backend) | $0-10 (pay per use) |
| Cloud Run (Frontend) | $0-5 (pay per use) |
| Artifact Registry | $0.10/GB |
| Secret Manager | $0.18 |
| **Total** | **~$10-30/month** |

## Security Checklist

- [ ] `DEBUG=false` in production
- [ ] `INIT_DEMO_DATA=false` in production
- [ ] Strong `SECRET_KEY` (64+ characters)
- [ ] Cloud SQL requires SSL (`--require-ssl`)
- [ ] Backend is not publicly accessible (`--no-allow-unauthenticated`)
- [ ] Service account has minimal permissions
- [ ] Secrets are in Secret Manager, not environment variables

## Files Reference

| File | Purpose |
|------|--------|
| `backend/Dockerfile.cloudrun` | Production backend image |
| `frontend/Dockerfile.cloudrun` | Production frontend image |
| `frontend/nginx.cloudrun.conf` | nginx config for Cloud Run |
| `cloudbuild.yaml` | CI/CD pipeline configuration |
| `deploy-cloudrun.sh` | Manual deployment script |
| `backend/.dockerignore` | Files excluded from backend image |
| `frontend/.dockerignore` | Files excluded from frontend image |
