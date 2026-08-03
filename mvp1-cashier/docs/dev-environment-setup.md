# DomOS MVP1 Cashier - Development Environment Setup

## Overview

This guide explains how to set up and run the DomOS MVP1 Cashier development environment inside an Agent Zero Docker container.

## Prerequisites

The Agent Zero container comes with:
- Python 3.x
- Node.js and npm
- PostgreSQL (may need to be started)

## Quick Start

### Automated Setup

The easiest way to start the development environment is using the provided scripts:

```bash
cd /a0/usr/projects/domos/mvp1-cashier

# Make scripts executable (first time only)
chmod +x start-dev-local.sh stop-dev-local.sh

# Start all services
./start-dev-local.sh

# Stop all services (keeps PostgreSQL running)
./stop-dev-local.sh

# Stop all services including PostgreSQL
./stop-dev-local.sh --all
```

### Manual Setup

If you prefer to set up manually or need to troubleshoot:

#### 1. Start PostgreSQL

```bash
# Start PostgreSQL service
service postgresql start

# Verify it's running
service postgresql status

# Or check the port
ss -tuln | grep 5432
```

#### 2. Create Database (if needed)

```bash
# Switch to postgres user and create database
su - postgres -c "createdb domos_cashier" 2>/dev/null || echo "Database may already exist"

# Set password for postgres user
su - postgres -c "psql -c \"ALTER USER postgres WITH PASSWORD 'postgres';\""
```

#### 3. Setup Backend

```bash
cd /a0/usr/projects/domos/mvp1-cashier/backend

# Create virtual environment (first time only)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file (first time only)
cat > .env << 'EOF'
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/domos_cashier
SECRET_KEY=dev-secret-key-change-in-production-min32chars
DEBUG=true
INIT_DEMO_DATA=true
DEMO_ADMIN_PASSWORD=admin123
DEMO_CASHIER_PASSWORD=cashier123
EOF

# Run database migrations
alembic upgrade head

# Initialize demo data
python init_db.py

# Start backend server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 4. Setup Frontend

In a new terminal:

```bash
cd /a0/usr/projects/domos/mvp1-cashier/frontend

# Install dependencies (first time only)
npm install

# Start frontend server
npm run dev -- --host 0.0.0.0
```

## Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:5173 | React application |
| Backend API | http://localhost:8000 | FastAPI server |
| API Docs | http://localhost:8000/docs | Swagger UI |
| API Redoc | http://localhost:8000/redoc | ReDoc documentation |

## Demo Users

| Username | Password | Role | Permissions |
|----------|----------|------|-------------|
| admin | admin123 | ADMIN | Full access |
| cashier | cashier123 | CASHIER | Payments, apartments |

## Database

### Connection Details

- **Host:** localhost
- **Port:** 5432
- **Database:** domos_cashier
- **Username:** postgres
- **Password:** postgres

### Useful Commands

```bash
# Connect to database
su - postgres -c "psql -d domos_cashier"

# List tables
su - postgres -c "psql -d domos_cashier -c '\dt'"

# Reset database (caution: deletes all data)
su - postgres -c "dropdb domos_cashier && createdb domos_cashier"
cd /a0/usr/projects/domos/mvp1-cashier/backend
source venv/bin/activate
alembic upgrade head
python init_db.py
```

## Logs

When using the automated scripts, logs are stored in:

- **Backend:** `/tmp/backend.log`
- **Frontend:** `/tmp/frontend.log`

To view logs in real-time:

```bash
# Backend logs
tail -f /tmp/backend.log

# Frontend logs
tail -f /tmp/frontend.log
```

## Troubleshooting

### PostgreSQL won't start

```bash
# Check if data directory exists
ls -la /var/lib/postgresql/data

# Initialize if empty
mkdir -p /var/lib/postgresql/data
chown -R postgres:postgres /var/lib/postgresql/data
chmod 700 /var/lib/postgresql/data
su - postgres -c "/usr/lib/postgresql/*/bin/initdb -D /var/lib/postgresql/data"

# Try starting again
service postgresql start
```

### Port already in use

```bash
# Find process using port 8000 (backend)
lsof -ti:8000 | xargs kill -9 2>/dev/null

# Find process using port 5173 (frontend)
lsof -ti:5173 | xargs kill -9 2>/dev/null
```

### Backend dependencies issues

```bash
cd /a0/usr/projects/domos/mvp1-cashier/backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Frontend dependencies issues

```bash
cd /a0/usr/projects/domos/mvp1-cashier/frontend
rm -rf node_modules package-lock.json
npm install
```

### Migration errors

```bash
cd /a0/usr/projects/domos/mvp1-cashier/backend
source venv/bin/activate

# Check current migration status
alembic current

# View migration history
alembic history

# If stuck, try stamping to latest
alembic stamp head
alembic upgrade head
```

## Development Workflow

1. **Start services:** `./start-dev-local.sh`
2. **Make code changes** in backend/frontend
3. **Backend:** Auto-reloads on Python file changes
4. **Frontend:** Auto-reloads on TypeScript/React changes
5. **Run tests:**
   - Backend: `cd backend && source venv/bin/activate && pytest`
   - Frontend: `cd frontend && npm test`
6. **Stop services:** `./stop-dev-local.sh`

## Notes

- The Agent Zero container does **not** support Docker-in-Docker
- All services run directly in the container, not in nested Docker containers
- PostgreSQL data persists in `/var/lib/postgresql/data`
- Backend virtual environment is in `backend/venv/`
- Frontend node_modules is in `frontend/node_modules/`
