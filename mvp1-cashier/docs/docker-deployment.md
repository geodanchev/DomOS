# DomOS Docker Deployment Guide

Този документ описва как да използвате автоматично генерираните Docker images за production deployment.

## CI/CD Pipeline

При всеки push към `main` или `master` branch, GitHub Actions автоматично:

1. **Изпълнява тестове** (backend и frontend)
2. **Build-ва Docker images** за backend и frontend
3. **Публикува images** в GitHub Container Registry (ghcr.io)

### Тагове на images

Images се публикуват със следните тагове:

| Събитие | Примерни тагове |
|---------|----------------|
| Push на main | `latest`, `main`, `<sha>` |
| Push на tag v1.2.3 | `1.2.3`, `1.2`, `<sha>` |
| Manual workflow | custom tag + `<sha>` |

### Image URLs

```
ghcr.io/<owner>/domos-backend:latest
ghcr.io/<owner>/domos-frontend:latest
```

## Deployment Options

### Option 1: Използване на готови GHCR images (препоръчително)

Използвайте `docker-compose.ghcr.yml` за production без локален build:

```bash
# 1. Подгответе .env.production файл
cp .env.production.example .env.production

# 2. Редактирайте .env.production с вашите настройки
nano .env.production

# 3. Pull на latest images
docker compose -f docker-compose.ghcr.yml pull

# 4. Стартирайте
docker compose -f docker-compose.ghcr.yml --env-file .env.production up -d
```

#### Конфигурация на .env.production

```env
# Required
DOMAIN=yourdomain.com
ACME_EMAIL=admin@yourdomain.com
POSTGRES_PASSWORD=your_secure_password
SECRET_KEY=your_jwt_secret_key

# Optional - image версия
IMAGE_TAG=latest
GITHUB_REPOSITORY_OWNER=geodanchev

# Optional - rate limits
RATE_LIMIT_API_AVG=100
RATE_LIMIT_API_BURST=50
RATE_LIMIT_AUTH_AVG=5
RATE_LIMIT_AUTH_BURST=10
```

### Option 2: Локален build (за development или custom changes)

Използвайте `docker-compose.prod.yml` за локален build:

```bash
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

## Обновяване на deployment

### С готови images:

```bash
# Pull новите images
docker compose -f docker-compose.ghcr.yml pull

# Рестарт с новите images
docker compose -f docker-compose.ghcr.yml --env-file .env.production up -d
```

### С конкретна версия:

```bash
# Задайте версията в .env.production
IMAGE_TAG=v1.2.3

# Или директно:
IMAGE_TAG=v1.2.3 docker compose -f docker-compose.ghcr.yml --env-file .env.production up -d
```

## Мониторинг

### Проверка на здравето на услугите:

```bash
# Статус на контейнерите
docker compose -f docker-compose.ghcr.yml ps

# Логове на backend
docker compose -f docker-compose.ghcr.yml logs -f backend

# Логове на frontend
docker compose -f docker-compose.ghcr.yml logs -f frontend

# Health check
curl https://yourdomain.com/health
```

### Traefik Dashboard:

Достъпен на `https://traefik.yourdomain.com` (изисква auth).

## Backup на базата данни

```bash
# Създаване на backup
docker compose -f docker-compose.ghcr.yml exec db pg_dump -U postgres domos_cashier > backup.sql

# Възстановяване от backup
cat backup.sql | docker compose -f docker-compose.ghcr.yml exec -T db psql -U postgres domos_cashier
```

## Troubleshooting

### Images не се pull-ват

Проверете дали имате достъп до GitHub Container Registry:

```bash
# Login в GHCR (за private repos)
echo $GITHUB_TOKEN | docker login ghcr.io -u $GITHUB_USER --password-stdin
```

### SSL сертификат не се генерира

1. Проверете дали DNS записът сочи към сървъра
2. Проверете дали портове 80 и 443 са отворени
3. Проверете Traefik логовете:

```bash
docker compose -f docker-compose.ghcr.yml logs traefik
```

### База данни не се свързва

```bash
# Проверка на db контейнера
docker compose -f docker-compose.ghcr.yml logs db

# Ръчно свързване
docker compose -f docker-compose.ghcr.yml exec db psql -U postgres
```

## Manual Workflow Trigger

Можете да trigger-нете Docker build ръчно от GitHub Actions:

1. Отидете на **Actions** → **Docker Build & Push**
2. Кликнете **Run workflow**
3. Опционално задайте custom tag
4. Кликнете **Run workflow**

## Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                        Internet                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Traefik (Reverse Proxy)                    │
│                   - SSL/TLS termination                      │
│                   - Rate limiting                            │
│                   - Let's Encrypt                            │
└─────────────────────────────────────────────────────────────┘
                    │                    │
                    ▼                    ▼
┌──────────────────────────┐  ┌──────────────────────────┐
│   Frontend (Nginx)       │  │   Backend (FastAPI)      │
│   - Static files         │  │   - REST API             │
│   - SPA routing          │  │   - Business logic       │
│   - GHCR image           │  │   - GHCR image           │
└──────────────────────────┘  └──────────────────────────┘
                                         │
                                         ▼
                              ┌──────────────────────────┐
                              │   PostgreSQL Database    │
                              │   - Persistent data      │
                              │   - Volume mounted       │
                              └──────────────────────────┘
```
