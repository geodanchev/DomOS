# DomOS Dev Deployment

Deploy DomOS Cashier MVP to a development environment. Use when the user wants to set up or start DomOS on a dev machine.

## When to Use

- User says: "deploy dev", "start dev environment", "setup DomOS", "run DomOS locally"
- User asks how to run DomOS on their machine
- User needs to set up a fresh dev environment

## Prerequisites

Verify these are installed on the target machine:

| Tool | Check Command | Min Version |
|------|---------------|-------------|
| Docker | `docker --version` | 20+ |
| Docker Compose | `docker compose version` | 2.0+ |
| Node.js | `node --version` | 18+ |
| npm | `npm --version` | 9+ |
| Git | `git --version` | 2.0+ |

## Step 1: Clone Repository

```bash
git clone https://github.com/geodanchev/DomOS.git
cd DomOS/mvp1-cashier
```

## Step 2: Fix Line Endings (WSL/Windows Only)

If running on WSL or Windows, fix CRLF line endings:

```bash
# Fix all shell scripts
sed -i 's/\r$//' start-dev.sh stop-dev.sh setup-db.sh reset-db.sh
sed -i 's/\r$//' backend/entrypoint.sh backend/entrypoint.prod.sh
sed -i 's/\r$//' backend/backup-db.sh backend/restore-db.sh backend/create-migration.sh

# Ensure executable permissions
chmod +x start-dev.sh stop-dev.sh setup-db.sh reset-db.sh
chmod +x backend/*.sh
```

## Step 3: Configure Environment

Create `.env.docker` file:

```bash
cat > .env.docker << 'EOF'
# Database
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=domos_cashier
DATABASE_URL=postgresql://postgres:postgres@db:5432/domos_cashier

# Backend
SECRET_KEY=dev-secret-key-change-in-production-32chars
ENVIRONMENT=development
DEBUG=true

# Frontend
VITE_API_URL=http://localhost:8000
EOF
```

## Step 4: Start Dev Environment

```bash
./start-dev.sh
```

This will:
1. 🐳 Start PostgreSQL container
2. 🔄 Auto-initialize database (migrations + users)
3. 🚀 Start backend (FastAPI) and frontend (Vite)

## Step 5: Verify Services

| Component | URL | Expected |
|-----------|-----|----------|
| Frontend | http://localhost:5173 | Login page |
| Backend API | http://localhost:8000 | API root |
| API Docs | http://localhost:8000/docs | Swagger UI |

## Default Login Credentials

| User | Password | Role |
|------|----------|------|
| `admin` | `admin123` | ADMIN |
| `cecka` | `1234` | CASHIER |

## Common Commands

```bash
# Start dev environment
./start-dev.sh

# Stop dev environment
./stop-dev.sh

# Check status
./status.sh

# Reset database (fresh start)
./reset-db.sh --with-demo-data

# View backend logs
docker compose -f docker-compose.dev.yml logs -f backend

# View all logs
docker compose -f docker-compose.dev.yml logs -f

# Restart specific service
docker compose -f docker-compose.dev.yml restart backend
```

## Database Management

```bash
# Connect to PostgreSQL
docker compose -f docker-compose.dev.yml exec db psql -U postgres -d domos_cashier

# Create backup
cd backend && ./backup-db.sh

# Restore backup
cd backend && ./restore-db.sh <backup_file>

# Create new migration
cd backend && ./create-migration.sh "description_of_changes"
```

## Troubleshooting

### Error: "required file not found" on scripts

**Cause:** CRLF line endings (Windows/WSL)

**Fix:**
```bash
sed -i 's/\r$//' <script_name>.sh
chmod +x <script_name>.sh
```

### Error: "Database not initialized"

**Cause:** First run or database was reset

**Fix:** The `start-dev.sh` should auto-initialize. If not:
```bash
./setup-db.sh --with-demo-data
```

### Error: "invalid input value for enum"

**Cause:** Enum mismatch between Python and PostgreSQL

**Fix:** Pull latest code and restart:
```bash
git pull
docker compose -f docker-compose.dev.yml restart backend
```

### Error: "Port already in use"

**Cause:** Another process using port 5173 or 8000

**Fix:**
```bash
# Find process
lsof -i :5173
lsof -i :8000

# Kill process or change ports in docker-compose.dev.yml
```

### Container won't start

**Fix:**
```bash
# Full restart
./stop-dev.sh
docker compose -f docker-compose.dev.yml down -v  # Removes volumes too
./start-dev.sh
```

## Updating Code

After pulling new changes:

```bash
git pull

# If backend dependencies changed
docker compose -f docker-compose.dev.yml build backend

# If frontend dependencies changed
docker compose -f docker-compose.dev.yml build frontend

# Restart
./stop-dev.sh && ./start-dev.sh
```

## Architecture Overview

```
mvp1-cashier/
├── backend/           # FastAPI Python backend
│   ├── app/
│   │   ├── api/       # API endpoints
│   │   ├── models/    # SQLAlchemy models
│   │   ├── schemas/   # Pydantic schemas
│   │   ├── services/  # Business logic
│   │   └── core/      # Config, security
│   ├── alembic/       # Database migrations
│   └── tests/         # Pytest tests
├── frontend/          # React + Vite frontend
│   └── src/
│       ├── pages/     # Page components
│       ├── components/ # UI components
│       └── services/  # API client
├── start-dev.sh       # Start dev environment
├── stop-dev.sh        # Stop dev environment
├── setup-db.sh        # Initialize database
└── reset-db.sh        # Reset database
```

## Key Rules

1. **Always** fix CRLF on WSL/Windows before running scripts
2. **Always** run `git pull` before starting work
3. **Never** modify `.env.docker` with production secrets
4. **Check** logs when something fails
5. **Use** `reset-db.sh` only when you need a fresh database
