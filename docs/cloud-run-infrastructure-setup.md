# DomOS Cloud Run Infrastructure Setup Guide

**Версия:** 1.0  
**Дата:** 2026-07-18  
**Проект:** bionic-region-502615-h8  
**Region:** europe-west3 (Frankfurt, Germany)

---

## 📋 Преглед

Това ръководство описва стъпките за настройка на Google Cloud инфраструктурата, необходима за хостване на DomOS в Cloud Run.

### Какво ще създадем:

| Компонент | Описание | Estimated Cost |
|-----------|----------|----------------|
| Artifact Registry | Docker image repository | ~$0.10/GB/month |
| Cloud SQL PostgreSQL | Managed database | ~$7-15/month (db-f1-micro) |
| Secret Manager | Credentials storage | ~$0.06/secret/month |
| Cloud Run Services | Application hosting | Pay-per-use |

### Предварителни изисквания:

- ✅ Google Cloud Project: `bionic-region-502615-h8`
- ✅ Billing account активиран
- ✅ gcloud CLI инсталиран и конфигуриран
- ✅ APIs активирани:
  - Cloud Run API
  - Artifact Registry API
  - Cloud SQL Admin API
  - Secret Manager API

---

## 🔧 Стъпка 1: Активиране на необходимите APIs

**Изпълни в Google Cloud Console или от терминал с Owner/Editor права:**

```bash
# Активиране на всички необходими APIs
gcloud services enable \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  sqladmin.googleapis.com \
  secretmanager.googleapis.com \
  cloudresourcemanager.googleapis.com \
  iam.googleapis.com \
  --project=bionic-region-502615-h8
```

**Проверка:**
```bash
gcloud services list --enabled \
  --filter="name:(run OR artifactregistry OR sqladmin OR secretmanager)" \
  --project=bionic-region-502615-h8
```

---

## 📦 Стъпка 2: Създаване на Artifact Registry Repository

Artifact Registry ще съхранява Docker images за backend и frontend.

### 2.1 Създаване на repository

```bash
gcloud artifacts repositories create domos \
  --repository-format=docker \
  --location=europe-west3 \
  --description="DomOS application container images" \
  --project=bionic-region-502615-h8
```

### 2.2 Проверка

```bash
gcloud artifacts repositories describe domos \
  --location=europe-west3 \
  --project=bionic-region-502615-h8
```

### 2.3 Docker authentication setup

```bash
# Configure Docker to use gcloud credentials for Artifact Registry
gcloud auth configure-docker europe-west3-docker.pkg.dev --quiet
```

### 2.4 Image naming convention

Images ще бъдат push-нати с формат:
```
europe-west3-docker.pkg.dev/bionic-region-502615-h8/domos/backend:v1.0.0
europe-west3-docker.pkg.dev/bionic-region-502615-h8/domos/frontend:v1.0.0
```

**Препоръка:** Използвай image digests вместо tags за production:
```
europe-west3-docker.pkg.dev/bionic-region-502615-h8/domos/backend@sha256:abc123...
```

---

## 🗄️ Стъпка 3: Създаване на Cloud SQL PostgreSQL Instance

Cloud SQL ще замени SQLite базата данни от development.

### 3.1 Създаване на instance

```bash
# Създаване на PostgreSQL 16 instance
# db-f1-micro е най-малката (и най-евтина) опция за development/small production
gcloud sql instances create domos-db \
  --database-version=POSTGRES_16 \
  --tier=db-f1-micro \
  --region=europe-west3 \
  --storage-type=SSD \
  --storage-size=10GB \
  --storage-auto-increase \
  --backup \
  --backup-start-time=03:00 \
  --availability-type=ZONAL \
  --assign-ip \
  --require-ssl \
  --project=bionic-region-502615-h8
```

**Очаквано време:** 3-5 минути

### 3.2 Проверка на instance status

```bash
gcloud sql instances describe domos-db \
  --project=bionic-region-502615-h8 \
  --format="table(name,state,region,databaseVersion,settings.tier)"
```

Изчакай докато `state` стане `RUNNABLE`.

### 3.3 Създаване на database

```bash
gcloud sql databases create domos \
  --instance=domos-db \
  --project=bionic-region-502615-h8
```

### 3.4 Генериране на secure password за database user

```bash
# Генерирай secure password (32 characters)
export DB_PASSWORD=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 32)
echo "Generated DB_PASSWORD: $DB_PASSWORD"
# ВАЖНО: Запиши тази парола на сигурно място!
```

### 3.5 Създаване на database user

```bash
gcloud sql users create domos_user \
  --instance=domos-db \
  --password="$DB_PASSWORD" \
  --project=bionic-region-502615-h8
```

### 3.6 Получаване на connection information

```bash
# Instance connection name (за Cloud Run)
gcloud sql instances describe domos-db \
  --project=bionic-region-502615-h8 \
  --format="value(connectionName)"
# Output: bionic-region-502615-h8:europe-west3:domos-db

# Public IP (за external connections с SSL, ако е нужно)
gcloud sql instances describe domos-db \
  --project=bionic-region-502615-h8 \
  --format="value(ipAddresses[0].ipAddress)"
```

### 3.7 Cloud SQL connection string format

За Cloud Run с Unix socket:
```
postgresql://domos_user:<PASSWORD>@/domos?host=/cloudsql/bionic-region-502615-h8:europe-west3:domos-db
```

За external connections с SSL:
```
postgresql://domos_user:<PASSWORD>@<PUBLIC_IP>:5432/domos?sslmode=require
```

---

## 🔐 Стъпка 4: Настройка на Secret Manager

Secret Manager ще съхранява всички sensitive credentials.

### 4.1 Генериране на SECRET_KEY за Django/FastAPI

```bash
# Генерирай secure secret key (64 characters)
export SECRET_KEY=$(openssl rand -base64 48 | tr -dc 'a-zA-Z0-9' | head -c 64)
echo "Generated SECRET_KEY: $SECRET_KEY"
# ВАЖНО: Запиши този ключ на сигурно място!
```

### 4.2 Създаване на secrets

```bash
# 1. Backend SECRET_KEY
echo -n "$SECRET_KEY" | gcloud secrets create domos-secret-key \
  --data-file=- \
  --replication-policy=automatic \
  --project=bionic-region-502615-h8

# 2. Database password
echo -n "$DB_PASSWORD" | gcloud secrets create domos-db-password \
  --data-file=- \
  --replication-policy=automatic \
  --project=bionic-region-502615-h8

# 3. Full database URL (за удобство на приложението)
export DATABASE_URL="postgresql://domos_user:${DB_PASSWORD}@/domos?host=/cloudsql/bionic-region-502615-h8:europe-west3:domos-db"
echo -n "$DATABASE_URL" | gcloud secrets create domos-database-url \
  --data-file=- \
  --replication-policy=automatic \
  --project=bionic-region-502615-h8
```

### 4.3 Проверка на създадените secrets

```bash
gcloud secrets list \
  --project=bionic-region-502615-h8 \
  --format="table(name,createTime)"
```

### 4.4 Тестване на secret достъп (optional)

```bash
# Прочитане на secret value (само за верификация)
gcloud secrets versions access latest \
  --secret=domos-secret-key \
  --project=bionic-region-502615-h8
```

---

## 👤 Стъпка 5: Настройка на Service Account и IAM

### 5.1 Service Accounts overview

| Service Account | Предназначение |
|-----------------|----------------|
| `id-domos-cloud-run-deployer` | Deployment operations (вече създаден) |
| `domos-backend-sa` | Cloud Run backend runtime identity |

### 5.2 Създаване на runtime Service Account за backend

```bash
# Създай dedicated service account за Cloud Run backend
gcloud iam service-accounts create domos-backend-sa \
  --display-name="DomOS Backend Runtime" \
  --description="Service account for DomOS backend Cloud Run service" \
  --project=bionic-region-502615-h8
```

### 5.3 Даване на необходимите роли на runtime SA

```bash
# Cloud SQL Client - за връзка към Cloud SQL
gcloud projects add-iam-policy-binding bionic-region-502615-h8 \
  --member="serviceAccount:domos-backend-sa@bionic-region-502615-h8.iam.gserviceaccount.com" \
  --role="roles/cloudsql.client"

# Secret Manager Secret Accessor - за четене на secrets
gcloud projects add-iam-policy-binding bionic-region-502615-h8 \
  --member="serviceAccount:domos-backend-sa@bionic-region-502615-h8.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Cloud Logging Writer - за писане на логове
gcloud projects add-iam-policy-binding bionic-region-502615-h8 \
  --member="serviceAccount:domos-backend-sa@bionic-region-502615-h8.iam.gserviceaccount.com" \
  --role="roles/logging.logWriter"

# Cloud Trace Agent - за tracing (optional)
gcloud projects add-iam-policy-binding bionic-region-502615-h8 \
  --member="serviceAccount:domos-backend-sa@bionic-region-502615-h8.iam.gserviceaccount.com" \
  --role="roles/cloudtrace.agent"
```

### 5.4 Даване на роли на deployer SA

```bash
# Cloud Run Admin - за deploy на услуги
gcloud projects add-iam-policy-binding bionic-region-502615-h8 \
  --member="serviceAccount:id-domos-cloud-run-deployer@bionic-region-502615-h8.iam.gserviceaccount.com" \
  --role="roles/run.admin"

# Service Account User - за deploy с други service accounts
gcloud projects add-iam-policy-binding bionic-region-502615-h8 \
  --member="serviceAccount:id-domos-cloud-run-deployer@bionic-region-502615-h8.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# Artifact Registry Writer - за push на images
gcloud projects add-iam-policy-binding bionic-region-502615-h8 \
  --member="serviceAccount:id-domos-cloud-run-deployer@bionic-region-502615-h8.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

# Secret Manager Viewer - за четене на secret metadata (не values)
gcloud projects add-iam-policy-binding bionic-region-502615-h8 \
  --member="serviceAccount:id-domos-cloud-run-deployer@bionic-region-502615-h8.iam.gserviceaccount.com" \
  --role="roles/secretmanager.viewer"

# Cloud SQL Admin - за управление на Cloud SQL
gcloud projects add-iam-policy-binding bionic-region-502615-h8 \
  --member="serviceAccount:id-domos-cloud-run-deployer@bionic-region-502615-h8.iam.gserviceaccount.com" \
  --role="roles/cloudsql.admin"

# Logs Viewer - за четене на логове
gcloud projects add-iam-policy-binding bionic-region-502615-h8 \
  --member="serviceAccount:id-domos-cloud-run-deployer@bionic-region-502615-h8.iam.gserviceaccount.com" \
  --role="roles/logging.viewer"
```

### 5.5 Проверка на IAM bindings

```bash
# За deployer SA
gcloud projects get-iam-policy bionic-region-502615-h8 \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:id-domos-cloud-run-deployer@bionic-region-502615-h8.iam.gserviceaccount.com" \
  --format="table(bindings.role)"

# За backend runtime SA
gcloud projects get-iam-policy bionic-region-502615-h8 \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:domos-backend-sa@bionic-region-502615-h8.iam.gserviceaccount.com" \
  --format="table(bindings.role)"
```

---

## ✅ Стъпка 6: Верификация на Infrastructure

### 6.1 Проверка на всички ресурси

```bash
echo "=== Artifact Registry ==="
gcloud artifacts repositories list \
  --location=europe-west3 \
  --project=bionic-region-502615-h8

echo "\n=== Cloud SQL Instances ==="
gcloud sql instances list \
  --project=bionic-region-502615-h8

echo "\n=== Cloud SQL Databases ==="
gcloud sql databases list \
  --instance=domos-db \
  --project=bionic-region-502615-h8

echo "\n=== Cloud SQL Users ==="
gcloud sql users list \
  --instance=domos-db \
  --project=bionic-region-502615-h8

echo "\n=== Secret Manager Secrets ==="
gcloud secrets list \
  --project=bionic-region-502615-h8

echo "\n=== Service Accounts ==="
gcloud iam service-accounts list \
  --project=bionic-region-502615-h8 \
  --filter="email:domos"

echo "\n=== Cloud Run Services ==="
gcloud run services list \
  --region=europe-west3 \
  --project=bionic-region-502615-h8
```

### 6.2 Тест на Cloud SQL connection

```bash
# Използвай Cloud SQL Proxy за local testing
# Инсталация: https://cloud.google.com/sql/docs/postgres/sql-proxy

# Start proxy
cloud_sql_proxy -instances=bionic-region-502615-h8:europe-west3:domos-db=tcp:5432 &

# Test connection (requires psql)
psql -h 127.0.0.1 -U domos_user -d domos -c "SELECT version();"
```

---

## 📋 Infrastructure Checklist

### APIs
- [ ] Cloud Run API enabled
- [ ] Artifact Registry API enabled
- [ ] Cloud SQL Admin API enabled
- [ ] Secret Manager API enabled
- [ ] Cloud Resource Manager API enabled
- [ ] IAM API enabled

### Artifact Registry
- [ ] Repository `domos` created in `europe-west3`
- [ ] Docker authentication configured

### Cloud SQL
- [ ] Instance `domos-db` created and RUNNABLE
- [ ] Database `domos` created
- [ ] User `domos_user` created
- [ ] Connection string generated and saved

### Secret Manager
- [ ] Secret `domos-secret-key` created
- [ ] Secret `domos-db-password` created
- [ ] Secret `domos-database-url` created

### IAM
- [ ] Runtime SA `domos-backend-sa` created
- [ ] Runtime SA has `cloudsql.client` role
- [ ] Runtime SA has `secretmanager.secretAccessor` role
- [ ] Runtime SA has `logging.logWriter` role
- [ ] Deployer SA has `run.admin` role
- [ ] Deployer SA has `iam.serviceAccountUser` role
- [ ] Deployer SA has `artifactregistry.writer` role

---

## 🔗 Quick Reference

### Key Values

| Resource | Value |
|----------|-------|
| Project ID | `bionic-region-502615-h8` |
| Project Number | `985395022174` |
| Region | `europe-west3` |
| Artifact Registry | `europe-west3-docker.pkg.dev/bionic-region-502615-h8/domos` |
| Cloud SQL Instance | `domos-db` |
| Cloud SQL Connection | `bionic-region-502615-h8:europe-west3:domos-db` |
| Database Name | `domos` |
| Database User | `domos_user` |
| Backend SA | `domos-backend-sa@bionic-region-502615-h8.iam.gserviceaccount.com` |
| Deployer SA | `id-domos-cloud-run-deployer@bionic-region-502615-h8.iam.gserviceaccount.com` |

### Secret Names

| Secret | Description |
|--------|-------------|
| `domos-secret-key` | FastAPI SECRET_KEY |
| `domos-db-password` | PostgreSQL user password |
| `domos-database-url` | Full connection string for Cloud Run |

### Image Naming

```bash
# Backend
europe-west3-docker.pkg.dev/bionic-region-502615-h8/domos/backend:v1.0.0

# Frontend
europe-west3-docker.pkg.dev/bionic-region-502615-h8/domos/frontend:v1.0.0
```

---

## 🚀 Следващи стъпки

След като infrastructure е готова:

1. **Адаптиране на приложението** - виж `docs/cloud-run-app-changes.md` (ще бъде създаден)
   - Backend PostgreSQL connection
   - Health check endpoints
   - Cloud Run PORT handling
   - Secret Manager integration

2. **Production Dockerfiles** - виж `docs/cloud-run-dockerfiles.md` (ще бъде създаден)
   - Multi-stage builds
   - Optimized images
   - PORT variable support

3. **CI/CD Pipeline** - виж `.github/workflows/cloud-run-deploy.yml` (ще бъде създаден)
   - Build и push към Artifact Registry
   - Deploy към Cloud Run

4. **Cloud Run Deployment** - използвай `cloud-run-operator` skill
   - Service YAML manifests
   - Staged deployment workflow

---

## 💰 Cost Estimation (Monthly)

| Resource | Tier | Estimated Cost |
|----------|------|----------------|
| Cloud SQL | db-f1-micro | ~$7-15 |
| Artifact Registry | Per GB | ~$0.10/GB |
| Secret Manager | 3 secrets | ~$0.18 |
| Cloud Run | Pay-per-use | ~$0-10 (low traffic) |
| **Total** | | **~$10-30/month** |

**Забележка:** Цените са приблизителни и зависят от реалното използване. Cloud Run има generous free tier (2 million requests/month).

---

## 📚 Useful Links

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud SQL for PostgreSQL](https://cloud.google.com/sql/docs/postgres)
- [Secret Manager](https://cloud.google.com/secret-manager/docs)
- [Artifact Registry](https://cloud.google.com/artifact-registry/docs)
- [IAM Roles Reference](https://cloud.google.com/iam/docs/understanding-roles)
- [Cloud Run Pricing](https://cloud.google.com/run/pricing)
- [Cloud SQL Pricing](https://cloud.google.com/sql/pricing)