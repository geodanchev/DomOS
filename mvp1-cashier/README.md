# DomOS Cashier MVP

**Дигитален касиер за етажна собственост** - управление на апартаменти, плащания и задължения.

## 🚀 Бързо стартиране с Docker

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+

### Production Mode

```bash
# 1. Копирайте environment файла
cp .env.docker .env

# 2. Редактирайте .env с вашите настройки (особено SECRET_KEY!)
nano .env

# 3. Стартирайте всички услуги
docker compose up -d

# 4. Проверете статуса
docker compose ps

# 5. Вижте логовете
docker compose logs -f
```

Приложението ще бъде достъпно на:
- **Frontend**: http://localhost (порт 80)
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Development Mode (с Hot Reload)

```bash
# Стартирайте в development режим
docker compose -f docker-compose.dev.yml up -d

# Следете логовете
docker compose -f docker-compose.dev.yml logs -f
```

В development режим:
- **Frontend**: http://localhost:5173 (Vite dev server с HMR)
- **Backend API**: http://localhost:8000 (с auto-reload)
- Промените в кода се отразяват автоматично

## 📁 Структура на проекта

```
mvp1-cashier/
├── backend/                 # FastAPI Backend
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Configuration, security
│   │   ├── db/             # Database session
│   │   ├── models/         # SQLAlchemy models
│   │   └── schemas/        # Pydantic schemas
│   ├── tests/              # Backend tests
│   ├── alembic/            # Database migrations
│   ├── Dockerfile          # Production Dockerfile
│   ├── Dockerfile.dev      # Development Dockerfile
│   ├── entrypoint.sh       # Startup script
│   └── requirements.txt    # Python dependencies
│
├── frontend/               # React Frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   ├── context/        # React context
│   │   └── types/          # TypeScript types
│   ├── Dockerfile          # Production Dockerfile (nginx)
│   ├── Dockerfile.dev      # Development Dockerfile (Vite)
│   ├── nginx.conf          # Nginx configuration
│   └── package.json        # Node dependencies
│
├── docker-compose.yml      # Production compose
├── docker-compose.dev.yml  # Development compose
├── .env.docker             # Environment template
└── README.md               # This file
```

## ⚙️ Конфигурация

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------||
| `POSTGRES_USER` | Database user | `postgres` |
| `POSTGRES_PASSWORD` | Database password | `postgres` |
| `POSTGRES_DB` | Database name | `domos_cashier` |
| `DB_PORT` | Database port | `5432` |
| `SECRET_KEY` | JWT secret key | *change in production!* |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry | `1440` (24h) |
| `DEBUG` | Debug mode | `false` |
| `BACKEND_PORT` | Backend port | `8000` |
| `FRONTEND_PORT` | Frontend port | `80` / `5173` |

### Database Migrations

Миграциите се изпълняват автоматично при стартиране на backend контейнера.

За ръчно управление:

```bash
# Влезте в backend контейнера
docker compose exec backend bash

# Създайте нова миграция
alembic revision --autogenerate -m "description"

# Приложете миграции
alembic upgrade head

# Отменете последната миграция
alembic downgrade -1
```

## 🔧 Полезни команди

```bash
# Стартиране
docker compose up -d

# Спиране
docker compose down

# Спиране с изтриване на volumes (ВНИМАНИЕ: изтрива данните!)
docker compose down -v

# Rebuild на images
docker compose build --no-cache

# Логове на конкретна услуга
docker compose logs -f backend
docker compose logs -f frontend
docker compose logs -f db

# Shell достъп до контейнер
docker compose exec backend bash
docker compose exec frontend sh
docker compose exec db psql -U postgres -d domos_cashier

# Рестарт на услуга
docker compose restart backend
```

## 🧪 Тестване

```bash
# Backend тестове
docker compose exec backend pytest

# Frontend тестове
docker compose exec frontend npm test
```

## 📊 Health Checks

Всички услуги имат health checks:

- **Database**: `pg_isready`
- **Backend**: `GET /health`
- **Frontend**: `wget http://localhost/`

```bash
# Проверка на здравето
docker compose ps
```

## 🔒 Production с HTTPS (Traefik + Let's Encrypt)

За production deployment с автоматичен SSL сертификат:

### Prerequisites

1. Домейн, насочен към вашия сървър
2. Отворени портове 80 и 443
3. Docker и Docker Compose

### Стъпки за deployment

```bash
# 1. Копирайте production environment файла
cp .env.production .env

# 2. Генерирайте сигурен SECRET_KEY
openssl rand -hex 32

# 3. Редактирайте .env с вашите настройки
nano .env
# Задължително сменете:
# - DOMAIN=your-domain.com
# - ACME_EMAIL=admin@your-domain.com
# - POSTGRES_PASSWORD=силна_парола
# - SECRET_KEY=генерираният_ключ

# 4. (По избор) Генерирайте Traefik dashboard парола
htpasswd -nb admin вашата_парола
# Копирайте резултата в TRAEFIK_DASHBOARD_AUTH в .env

# 5. Стартирайте production stack
docker compose -f docker-compose.prod.yml up -d

# 6. Проверете статуса
docker compose -f docker-compose.prod.yml ps

# 7. Следете логовете
docker compose -f docker-compose.prod.yml logs -f
```

### Достъп след deployment

| Услуга | URL |
|--------|-----|
| **Приложение** | https://your-domain.com |
| **API** | https://your-domain.com/api |
| **API Docs** | https://your-domain.com/docs |
| **Traefik Dashboard** | https://traefik.your-domain.com |

### Включени функции

- ✅ **Автоматичен SSL** - Let's Encrypt сертификати
- ✅ **HTTP→HTTPS redirect** - всички заявки към HTTPS
- ✅ **WWW redirect** - www.domain.com → domain.com
- ✅ **Security headers** - HSTS, XSS protection, clickjacking prevention
- ✅ **Health checks** - автоматичен мониторинг
- ✅ **Auto-restart** - рестарт при падане

### Сигурност

1. **Сменете `SECRET_KEY`** - използвайте `openssl rand -hex 32`
2. **Сменете паролата на базата** - не използвайте default стойности
3. **Сменете Traefik dashboard паролата** - или деактивирайте dashboard-а
4. **Ограничете достъпа** - използвайте firewall (ufw/iptables)
5. **Редовни backups** - backup-вайте PostgreSQL data volume
6. **Мониторинг** - следете логовете и health checks

## 📝 API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🐛 Troubleshooting

### Database connection issues

```bash
# Проверете дали базата е стартирана
docker compose ps db

# Проверете логовете
docker compose logs db

# Рестартирайте услугите
docker compose restart
```

### Frontend не се зарежда

```bash
# Проверете build logs
docker compose logs frontend

# Rebuild frontend
docker compose build frontend --no-cache
docker compose up -d frontend
```

### Backend грешки

```bash
# Проверете логовете
docker compose logs backend

# Влезте в контейнера за дебъг
docker compose exec backend bash
```

---

**DomOS** - Дигитализация на етажната собственост 🏢
