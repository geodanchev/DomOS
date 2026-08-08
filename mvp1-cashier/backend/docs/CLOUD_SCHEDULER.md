# Cloud Scheduler - Автоматично генериране на месечни задължения

## Обзор

Cloud Scheduler се използва за автоматично генериране на месечни задължения за всички апартаменти на 1-во число от всеки месец.

### Защо Cloud Scheduler вместо APScheduler?

APScheduler работи в паметта на процеса и не е подходящ за Cloud Run защото:
- Cloud Run instances могат да се scale to zero
- При рестарт на контейнера scheduler-ът губи състоянието си
- Няма гаранция, че instance-ът ще е active на 1-во число

Cloud Scheduler е managed service който:
- Работи независимо от Cloud Run instances
- Гарантира изпълнение дори ако service-ът е scaled to zero
- Поддържа retry logic и logging

## Архитектура

```
┌─────────────────────┐     OIDC Token      ┌──────────────────────┐
│   Cloud Scheduler   │ ───────────────────► │   Cloud Run Backend  │
│                     │    POST /api/cron/   │                      │
│  Cron: 5 0 1 * *    │  generate-monthly-   │  /api/cron/generate- │
│  (1st day, 00:05)   │     obligations      │  monthly-obligations │
└─────────────────────┘                      └──────────────────────┘
         │                                              │
         │                                              ▼
         │                                   ┌──────────────────────┐
         │                                   │  ObligationService   │
         │                                   │                      │
         │                                   │  generate_monthly_   │
         │                                   │    obligations()     │
         │                                   └──────────────────────┘
         │
         ▼
┌─────────────────────┐
│  Service Account    │
│  cloud-scheduler-   │
│      invoker        │
│                     │
│  roles/run.invoker  │
└─────────────────────┘
```

## Компоненти

### 1. Cron Endpoint (`/api/cron/generate-monthly-obligations`)

**Файл:** `app/api/cron.py`

Този endpoint е специално проектиран за Cloud Scheduler:
- Приема OIDC token authentication (не JWT)
- Валидира, че заявката идва от оторизиран service account
- Поддържа и CRON_SECRET header за development/testing

### 2. Setup Script

**Файл:** `scripts/setup-cloud-scheduler.sh`

Създава:
- Service account `cloud-scheduler-invoker` с `roles/run.invoker`
- Cloud Scheduler job с cron expression `5 0 1 * *`

### 3. Config Settings

**Файл:** `app/core/config.py`

Нови полета:
- `GCP_PROJECT_ID` - ID на GCP проекта
- `GCP_PROJECT_NUMBER` - Номер на GCP проекта
- `BACKEND_URL` - URL на Cloud Run backend service-а

## Инсталация

### Prerequisite: Деплойнат backend с новия cron endpoint

```bash
# Деплойни backend
cd /a0/usr/projects/domos/mvp1-cashier
./deploy-cloudrun.sh
```

### Setup Cloud Scheduler

```bash
cd /a0/usr/projects/domos/mvp1-cashier/backend/scripts
./setup-cloud-scheduler.sh
```

Скриптът автоматично:
1. Взема URL на backend service-а
2. Създава service account (ако не съществува)
3. Дава `roles/run.invoker` на service account-а
4. Създава Cloud Scheduler job

## Тестване

### Ръчно тригериране

```bash
gcloud scheduler jobs run domos-monthly-obligations \
  --project=bionic-region-502615-h8 \
  --location=europe-west1
```

### Проверка на логове

```bash
# Cloud Scheduler логове
gcloud logging read 'resource.type=cloud_scheduler_job' \
  --project=bionic-region-502615-h8 \
  --limit=10

# Cloud Run логове за cron endpoint
gcloud logging read 'resource.type=cloud_run_revision AND textPayload:"Cloud Scheduler"' \
  --project=bionic-region-502615-h8 \
  --limit=10
```

### Тестване с CRON_SECRET (development)

```bash
# Сетни CRON_SECRET в Cloud Run
gcloud run services update domos-cashier-backend \
  --project=bionic-region-502615-h8 \
  --region=europe-west3 \
  --set-env-vars="CRON_SECRET=your-secret-here"

# Тествай локално
curl -X POST https://domos-cashier-backend-qoagunxmwa-ey.a.run.app/api/cron/generate-monthly-obligations \
  -H "X-Cron-Secret: your-secret-here"
```

## Security

### OIDC Token Validation

Endpoint-ът валидира:
1. Authorization header с Bearer token
2. Token е валиден OIDC token от Google
3. Token audience съвпада с BACKEND_URL
4. Service account email е от позволен domain/list

### Позволени Service Accounts

```python
ALLOWED_SA_DOMAINS = [
    f"@{GCP_PROJECT_ID}.iam.gserviceaccount.com",
    "@developer.gserviceaccount.com",
    "@cloudbuild.gserviceaccount.com",
]
```

### CRON_SECRET (Опционално)

За допълнителна защита може да се сетне `CRON_SECRET` environment variable.
Това позволява тестване от development среди.

## Troubleshooting

### Job не се изпълнява

1. Провери статуса на job:
   ```bash
   gcloud scheduler jobs describe domos-monthly-obligations \
     --project=bionic-region-502615-h8 \
     --location=europe-west1
   ```

2. Провери последните изпълнения:
   ```bash
   gcloud logging read 'resource.type=cloud_scheduler_job AND resource.labels.job_id=domos-monthly-obligations' \
     --project=bionic-region-502615-h8 \
     --limit=5
   ```

### 401 Unauthorized

- Провери дали service account-ът има `roles/run.invoker`
- Провери дали OIDC audience съвпада с BACKEND_URL
- Провери Cloud Run логовете за детайли

### 500 Internal Server Error

- Провери backend логовете
- Провери database connectivity
- Провери дали има апартаменти в базата

## Мониторинг

### Cloud Monitoring

Създай alert за:
- Failed Cloud Scheduler executions
- 4xx/5xx responses от cron endpoint-а
- Липса на нови задължения след 1-во число

### Примерен alert query:

```
resource.type="cloud_scheduler_job"
resource.labels.job_id="domos-monthly-obligations"
severity>=WARNING
```
