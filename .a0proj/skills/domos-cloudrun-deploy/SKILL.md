# DomOS Cloud Run Deploy

Автоматичен deployment workflow за DomOS проекта в Google Cloud Run с CI/CD интеграция и rollback възможности.

## Trigger Phrases

- "deploy to cloud run"
- "deploy нова версия"
- "пусни на production"
- "update cloud run"
- "деплойни в cloud"
- "push and deploy"
- "rollback deployment"
- "върни предишната версия"

## Prerequisites

- GCP Project: `bionic-region-502615-h8`
- Region: `europe-west3`
- Artifact Registry: `europe-west3-docker.pkg.dev/bionic-region-502615-h8/domos`
- Cloud SQL: `domos-db` (PostgreSQL 16)
- Services: `domos-cashier-backend`, `domos-cashier-frontend`

## Workflow Overview

### Option 1: Full Deploy (Git + Cloud Run)

1. **Check for uncommitted changes**
2. **Ask for branch** (default: `main`)
3. **Git commit & push** (uses domos-git-push skill logic)
4. **Trigger Cloud Build** or run deploy script
5. **Wait for build completion**
6. **Health check** new services
7. **Report status** with URLs

### Option 2: Deploy Only (no git)

1. **Ask for branch** (default: `main`)
2. **Run deploy script**
3. **Health check** new services
4. **Report status**

### Option 3: Rollback

1. **List available revisions**
2. **Select revision to rollback to**
3. **Execute rollback**
4. **Verify rollback**

## Step-by-Step Instructions

### Step 1: Check Git Status

```bash
cd /a0/usr/projects/domos
git status
```

If there are uncommitted changes, ask user:
- "Има uncommitted промени. Искате ли да ги commit-на и push-на преди deploy?"

### Step 2: Ask for Branch

Default is `main`. Ask user:
- "Кой branch да deploy-на? (default: main)"

If user doesn't specify, use `main`.

### Step 3: Git Push (if needed)

Follow domos-git-push skill for:
- Staging files (exclude `.a0proj/memory/*`)
- Creating commit
- Push with correct PAT token

```bash
# Check for workflow files
git diff --cached --name-only | grep -E '\.github/workflows/' && USE_WORKFLOW_TOKEN=true

# Push with appropriate token
# If workflow files: use GIT_PAT_WORKFLOW
# Otherwise: use GIT_PAT
```

### Step 4: Deploy to Cloud Run

**Option A: Using deploy script (recommended)**

```bash
cd /a0/usr/projects/domos/mvp1-cashier
./deploy-cloudrun.sh
```

**Option B: Manual gcloud commands**

```bash
# Set project
gcloud config set project bionic-region-502615-h8

# Build and deploy backend
cd /a0/usr/projects/domos/mvp1-cashier/backend
gcloud builds submit \
  --tag europe-west3-docker.pkg.dev/bionic-region-502615-h8/domos/backend:$(git rev-parse --short HEAD) \
  -f Dockerfile.cloudrun

gcloud run deploy domos-cashier-backend \
  --image europe-west3-docker.pkg.dev/bionic-region-502615-h8/domos/backend:$(git rev-parse --short HEAD) \
  --region europe-west3 \
  --platform managed

# Build and deploy frontend
cd /a0/usr/projects/domos/mvp1-cashier/frontend
gcloud builds submit \
  --tag europe-west3-docker.pkg.dev/bionic-region-502615-h8/domos/frontend:$(git rev-parse --short HEAD) \
  -f Dockerfile.cloudrun

gcloud run deploy domos-cashier-frontend \
  --image europe-west3-docker.pkg.dev/bionic-region-502615-h8/domos/frontend:$(git rev-parse --short HEAD) \
  --region europe-west3 \
  --platform managed \
  --allow-unauthenticated
```

### Step 5: Health Check

```bash
# Check backend health
curl -s https://domos-cashier-backend-qoagunxmwa-ey.a.run.app/health | jq .

# Check frontend
curl -s -o /dev/null -w "%{http_code}" https://domos-cashier-frontend-qoagunxmwa-ey.a.run.app/
```

### Step 6: Verify Deployment

```bash
# List current revisions
gcloud run revisions list --service domos-cashier-backend --region europe-west3 --limit 3
gcloud run revisions list --service domos-cashier-frontend --region europe-west3 --limit 3

# Check service status
gcloud run services describe domos-cashier-backend --region europe-west3 --format='value(status.url)'
gcloud run services describe domos-cashier-frontend --region europe-west3 --format='value(status.url)'
```

## Rollback Procedure

### Step 1: List Available Revisions

```bash
# Backend revisions
gcloud run revisions list \
  --service domos-cashier-backend \
  --region europe-west3 \
  --format='table(name,active,createTime)' \
  --limit 10

# Frontend revisions
gcloud run revisions list \
  --service domos-cashier-frontend \
  --region europe-west3 \
  --format='table(name,active,createTime)' \
  --limit 10
```

### Step 2: Execute Rollback

```bash
# Rollback backend to specific revision
gcloud run services update-traffic domos-cashier-backend \
  --region europe-west3 \
  --to-revisions=<REVISION_NAME>=100

# Rollback frontend to specific revision
gcloud run services update-traffic domos-cashier-frontend \
  --region europe-west3 \
  --to-revisions=<REVISION_NAME>=100
```

### Step 3: Verify Rollback

```bash
# Check current serving revision
gcloud run services describe domos-cashier-backend \
  --region europe-west3 \
  --format='value(status.traffic[0].revisionName)'

gcloud run services describe domos-cashier-frontend \
  --region europe-west3 \
  --format='value(status.traffic[0].revisionName)'
```

## Quick Rollback (Last Known Good)

If deployment fails, rollback to previous revision:

```bash
# Get previous revision names
BACKEND_PREV=$(gcloud run revisions list --service domos-cashier-backend --region europe-west3 --format='value(name)' --limit 2 | tail -1)
FRONTEND_PREV=$(gcloud run revisions list --service domos-cashier-frontend --region europe-west3 --format='value(name)' --limit 2 | tail -1)

# Rollback
gcloud run services update-traffic domos-cashier-backend --region europe-west3 --to-revisions=$BACKEND_PREV=100
gcloud run services update-traffic domos-cashier-frontend --region europe-west3 --to-revisions=$FRONTEND_PREV=100

echo "Rolled back to: Backend=$BACKEND_PREV, Frontend=$FRONTEND_PREV"
```

## CI/CD: Cloud Build Trigger Setup

To enable automatic deployment on push:

### Create Cloud Build Trigger

```bash
# Create trigger for main branch
gcloud builds triggers create github \
  --repo-name=DomOS \
  --repo-owner=geodanchev \
  --branch-pattern='^main$' \
  --build-config=mvp1-cashier/cloudbuild.yaml \
  --name=domos-deploy-main \
  --region=europe-west3
```

### Trigger Configuration

The `cloudbuild.yaml` is already configured at `/a0/usr/projects/domos/mvp1-cashier/cloudbuild.yaml`.

It will:
1. Build backend Docker image
2. Push to Artifact Registry
3. Deploy backend to Cloud Run
4. Build frontend Docker image
5. Push to Artifact Registry
6. Deploy frontend to Cloud Run

## Production URLs

| Service | URL |
|---------|-----|
| **Frontend** | https://domos-cashier-frontend-qoagunxmwa-ey.a.run.app |
| **Backend** | https://domos-cashier-backend-qoagunxmwa-ey.a.run.app |
| **Backend Health** | https://domos-cashier-backend-qoagunxmwa-ey.a.run.app/health |
| **Backend API Docs** | https://domos-cashier-backend-qoagunxmwa-ey.a.run.app/docs |

## Troubleshooting

### Build Fails

```bash
# Check build logs
gcloud builds list --limit 5
gcloud builds log <BUILD_ID>
```

### Service Not Responding

```bash
# Check service logs
gcloud run services logs read domos-cashier-backend --region europe-west3 --limit 50
gcloud run services logs read domos-cashier-frontend --region europe-west3 --limit 50
```

### Database Connection Issues

```bash
# Verify Cloud SQL connection
gcloud sql instances describe domos-db --format='value(connectionName)'
# Should be: bionic-region-502615-h8:europe-west3:domos-db
```

## Agent Workflow Summary

When user asks to deploy:

1. **Ask**: "Кой branch да deploy-на? (default: main)"
2. **Check**: `git status` for uncommitted changes
3. **If changes**: Ask to commit & push first
4. **Deploy**: Run `./deploy-cloudrun.sh`
5. **Verify**: Health check + revision list
6. **Report**: Show URLs and status

When user asks to rollback:

1. **List**: Show available revisions with dates
2. **Ask**: Which revision to rollback to
3. **Execute**: `gcloud run services update-traffic`
4. **Verify**: Confirm serving revision changed
5. **Report**: Show current status

## Files Reference

- Deploy script: `/a0/usr/projects/domos/mvp1-cashier/deploy-cloudrun.sh`
- Cloud Build config: `/a0/usr/projects/domos/mvp1-cashier/cloudbuild.yaml`
- Backend Dockerfile: `/a0/usr/projects/domos/mvp1-cashier/backend/Dockerfile.cloudrun`
- Frontend Dockerfile: `/a0/usr/projects/domos/mvp1-cashier/frontend/Dockerfile.cloudrun`
- Infrastructure docs: `/a0/usr/projects/domos/docs/cloud-run-infrastructure-setup.md`
- Deployment guide: `/a0/usr/projects/domos/mvp1-cashier/CLOUD_RUN_DEPLOYMENT.md`
