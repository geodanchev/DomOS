# DomOS Backup Strategy

Комплексна стратегия за backup и disaster recovery на Cloud SQL базата данни.

## Съдържание

1. [Преглед](#преглед)
2. [Автоматични Backups (Cloud SQL)](#автоматични-backups-cloud-sql)
3. [Ръчни Backups](#ръчни-backups)
4. [Restore процедури](#restore-процедури)
5. [Backup преди Deploy](#backup-преди-deploy)
6. [Мониторинг](#мониторинг)
7. [Disaster Recovery Plan](#disaster-recovery-plan)

---

## Преглед

### Backup Types

| Тип | Честота | Retention | Използване |
|-----|---------|-----------|------------|
| **Automated** | Ежедневно | 7 дни | Стандартен recovery |
| **On-demand** | При нужда | До изтриване | Преди deployments, миграции |
| **Point-in-time** | Continuous | 7 дни | Прецизен recovery |

### Recovery Time Objectives

- **RTO (Recovery Time Objective)**: < 30 минути
- **RPO (Recovery Point Objective)**: < 24 часа (автоматични) / < 1 час (on-demand)

---

## Автоматични Backups (Cloud SQL)

### Текуща конфигурация

```
Project: bionic-region-502615-h8
Instance: domos-db
Region: europe-west3
Database: domos
```

### Включване на автоматични backups

Ако не са включени, изпълнете:

```bash
# Включи автоматични backups с 7-дневен retention
gcloud sql instances patch domos-db \
    --backup-start-time=03:00 \
    --enable-bin-log \
    --retained-backups-count=7 \
    --retained-transaction-log-days=7 \
    --project=bionic-region-502615-h8
```

### Проверка на конфигурацията

```bash
# Виж текущата backup конфигурация
gcloud sql instances describe domos-db \
    --format="yaml(settings.backupConfiguration)" \
    --project=bionic-region-502615-h8
```

### Очаквана конфигурация

```yaml
settings:
  backupConfiguration:
    enabled: true
    startTime: "03:00"              # 03:00 UTC
    binaryLogEnabled: true           # За point-in-time recovery
    location: eu                     # Backup storage location
    transactionLogRetentionDays: 7   # За PITR
    backupRetentionSettings:
      retainedBackups: 7             # 7 дни retention
```

---

## Ръчни Backups

### Кога да правите on-demand backup

- ✅ Преди major deployment
- ✅ Преди database migration
- ✅ Преди bulk data operations
- ✅ Преди ръчни SQL промени
- ✅ След важни бизнес операции (годишно приключване)

### Използване на скрипта

```bash
# От локална машина с gcloud CLI
cd mvp1-cashier/backend/scripts
./cloud-sql-backup.sh "Pre-deployment backup v1.2.0"

# Или директно с gcloud
gcloud sql backups create \
    --instance=domos-db \
    --description="Pre-deployment backup v1.2.0" \
    --project=bionic-region-502615-h8
```

### Списък на backups

```bash
# Виж всички налични backups
gcloud sql backups list \
    --instance=domos-db \
    --project=bionic-region-502615-h8 \
    --format="table(id, windowStartTime, status, description)"
```

### Cloud Console

Backups могат да се управляват и от Cloud Console:
https://console.cloud.google.com/sql/instances/domos-db/backups?project=bionic-region-502615-h8

---

## Restore процедури

### ⚠️ ВНИМАНИЕ

> **Restore операция ще ИЗТРИЕ всички текущи данни и ще ги замени с данните от backup-а!**

### Restore от backup

```bash
# 1. Списък на налични backups
gcloud sql backups list --instance=domos-db

# 2. Идентифицирай backup ID (напр. 1719475200000)

# 3. Restore (ВНИМАНИЕ: деструктивна операция!)
gcloud sql backups restore BACKUP_ID \
    --restore-instance=domos-db \
    --backup-instance=domos-db \
    --project=bionic-region-502615-h8
```

### Restore до определен момент (Point-in-Time Recovery)

```bash
# Restore до конкретен timestamp
gcloud sql instances restore-backup domos-db \
    --restore-point="2026-07-27T14:00:00.000Z" \
    --project=bionic-region-502615-h8
```

### Използване на restore скрипта

```bash
cd mvp1-cashier/backend/scripts
./cloud-sql-restore.sh
```

Скриптът е интерактивен и изисква потвърждение.

### След restore

1. **Провери данните** - влез в Cloud SQL Studio и верифицирай
2. **Рестартирай Cloud Run** - за да презареди connections
   ```bash
   gcloud run services update domos-cashier-backend \
       --region=europe-west3 \
       --no-traffic
   # После върни traffic-а
   gcloud run services update-traffic domos-cashier-backend \
       --region=europe-west3 \
       --to-latest
   ```
3. **Тествай приложението** - направи smoke test
4. **Провери reconciliation** - изпълни GET /api/admin/reconcile-balances

---

## Backup преди Deploy

### Автоматизиран pre-deploy backup

Добавете в `deploy-cloudrun.sh`:

```bash
# Pre-deployment backup
echo "[0/8] Creating pre-deployment backup..."
BACKUP_DESC="Pre-deploy $(git rev-parse --short HEAD) $(date +%Y%m%d-%H%M%S)"
gcloud sql backups create \
    --instance=domos-db \
    --description="${BACKUP_DESC}" \
    --async \
    --project=${PROJECT_ID}
echo "Backup initiated: ${BACKUP_DESC}"
```

### Cloud Build Integration

В `cloudbuild.yaml` добавете step преди deploy:

```yaml
# Step: Pre-deployment backup
- id: 'backup-database'
  name: 'gcr.io/cloud-builders/gcloud'
  args:
    - 'sql'
    - 'backups'
    - 'create'
    - '--instance=domos-db'
    - '--description=Pre-deploy ${_TAG} ${BUILD_ID}'
    - '--async'
  waitFor: ['build-info']
```

---

## Мониторинг

### Cloud Monitoring Alerts

Създайте alerts за backup проблеми:

```bash
# Създай alert policy за failed backups
gcloud alpha monitoring policies create \
    --display-name="Cloud SQL Backup Failures" \
    --condition-display-name="Backup failed" \
    --condition-filter='resource.type="cloudsql_database" AND metric.type="cloudsql.googleapis.com/database/backup/success" AND metric.labels.status="FAILED"' \
    --notification-channels="YOUR_CHANNEL_ID" \
    --project=bionic-region-502615-h8
```

### Ръчна проверка

```bash
# Провери последните backups
gcloud sql backups list \
    --instance=domos-db \
    --limit=5 \
    --format="table(id, windowStartTime, status)"
```

---

## Disaster Recovery Plan

### Сценарий 1: Corrupted Data

1. **Идентифицирай** кога са корумпирани данните
2. **Намери** последния добър backup преди корупцията
3. **Уведоми** потребителите за planned downtime
4. **Restore** от backup
5. **Верифицирай** данните
6. **Анализирай** root cause

### Сценарий 2: Accidental Deletion

1. **СПРИ** веднага всички write операции
2. **Оцени** какво е изтрито
3. За малки промени - ръчно възстанови
4. За големи промени - restore от backup
5. **Документирай** инцидента

### Сценарий 3: Instance Failure

1. Cloud SQL има автоматичен failover (ако е HA)
2. За single instance - Google ще възстанови автоматично
3. При дълъг outage - създай нов instance от backup

### Контакти при инцидент

| Role | Contact |
|------|--------|
| Project Owner | [TBD] |
| Database Admin | [TBD] |
| On-call Dev | [TBD] |

---

## Чеклист

### Weekly

- [ ] Провери дали автоматичните backups работят
- [ ] Верифицирай backup count (трябва да има поне 7)

### Before Major Changes

- [ ] Създай on-demand backup с описателно име
- [ ] Изчакай backup да завърши
- [ ] Запиши backup ID за reference

### Monthly

- [ ] Тествай restore процедурата в staging environment
- [ ] Review и update на disaster recovery план
- [ ] Провери backup storage costs

---

## Полезни команди

```bash
# Статус на instance
gcloud sql instances describe domos-db --format="yaml(state, settings.backupConfiguration)"

# Списък backups
gcloud sql backups list --instance=domos-db

# Създай backup
gcloud sql backups create --instance=domos-db --description="Manual backup"

# Изтрий стар backup (внимателно!)
gcloud sql backups delete BACKUP_ID --instance=domos-db

# Restore от backup
gcloud sql backups restore BACKUP_ID --restore-instance=domos-db --backup-instance=domos-db
```

---

## Версии

| Версия | Дата | Промени |
|--------|------|---------|
| 1.0 | 2026-07-27 | Initial backup strategy |
