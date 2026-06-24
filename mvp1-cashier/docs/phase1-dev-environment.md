# Phase 1: DEV Environment Setup

## Overview

Phase 1 implements an automated and idempotent database initialization workflow for the DomOS Cashier MVP development environment.

**Estimated Implementation Time:** ~2-3 hours ✅ **COMPLETED**

## What Was Implemented

### 1. `setup-db.sh` - Database Setup Script

**Location:** `/mvp1-cashier/setup-db.sh`

**Purpose:** Comprehensive database initialization script that handles schema creation and optional demo data loading.

**Features:**
- ✅ Checks if database container is running (starts it if needed)
- ✅ Waits for database to be ready with health checks
- ✅ Runs Alembic migrations (`alembic upgrade head`)
- ✅ Creates essential users (admin, cecka) by default
- ✅ Supports `--with-demo-data` flag for full demo data (apartments, obligations, payments)
- ✅ Supports `--fresh` flag for complete database reset
- ✅ Works with both backend container and local Python environment
- ✅ Color-coded output for better readability
- ✅ Detailed success/error reporting

**Usage:**
```bash
# Basic setup (users only)
./setup-db.sh

# Setup with full demo data
./setup-db.sh --with-demo-data

# Fresh install (drop all tables first)
./setup-db.sh --fresh

# Fresh install with demo data
./setup-db.sh --fresh --with-demo-data
```

**Output Example:**
```
════════════════════════════════════════════════════════════
   DomOS Database Setup
════════════════════════════════════════════════════════════

✓ Docker is running
✓ Database container is running
✓ Database is ready
📊 Running database migrations...
✓ Database schema updated
👥 Creating users only...
✓ Created admin user
✓ Created cashier user (Цецка)

════════════════════════════════════════════════════════════
✅ Database setup completed successfully!
════════════════════════════════════════════════════════════

Database connection:
  Host:     localhost
  Port:     5432
  Database: domos_cashier
  User:     postgres

Users created:
  ✓ admin (password: admin123)
  ✓ cecka (password: 1234)

Note: No apartments or obligations loaded.
      Use --with-demo-data flag to load full demo data.
════════════════════════════════════════════════════════════
```

### 2. `init_users_only.py` - Minimal User Initialization

**Location:** `/mvp1-cashier/backend/init_users_only.py`

**Purpose:** Idempotent script that creates only essential users without any demo data.

**Features:**
- ✅ Creates only two users: `admin` and `cecka`
- ✅ Idempotent - safe to run multiple times
- ✅ Skips creation if users already exist
- ✅ Shows existing users when skipping
- ✅ No apartments, obligations, or payments
- ✅ Clean, minimal output

**Users Created:**
- **admin** (role: ADMIN, password: admin123)
- **cecka** (role: CASHIER, password: 1234)

**Usage:**
```bash
# From backend directory
cd backend
python init_users_only.py

# Or via Docker
docker exec domos-backend-dev python init_users_only.py
```

### 3. Modified `start-dev.sh` - Enhanced Development Startup

**Location:** `/mvp1-cashier/start-dev.sh`

**Enhancements:**
- ✅ Automatic database initialization check on first run
- ✅ Runs `setup-db.sh` automatically if database is empty
- ✅ Supports `--fresh` flag for database reset
- ✅ Better error handling and health checks
- ✅ Improved wait logic for database readiness
- ✅ Clear status messages throughout startup

**New Workflow:**
```bash
# First run (fresh environment)
./start-dev.sh
# → Detects empty database
# → Automatically runs setup-db.sh
# → Creates users
# → Starts backend and frontend

# Subsequent runs (database already initialized)
./start-dev.sh
# → Detects existing tables
# → Skips initialization
# → Starts services directly

# Force fresh database reset
./start-dev.sh --fresh
# → Drops all tables
# → Runs setup-db.sh --fresh
# → Recreates everything
# → Starts services
```

## Implementation Details

### Architecture Decisions

1. **Idempotent Design**
   - All scripts can be run multiple times safely
   - Checks prevent duplicate data creation
   - Clear skip messages when data exists

2. **Flexible Execution Context**
   - Scripts work with backend container when running
   - Fall back to local Python environment if container is not available
   - Automatic virtual environment activation

3. **Progressive Enhancement**
   - Default: minimal setup (users only)
   - Optional: full demo data with `--with-demo-data`
   - Destructive: fresh install with `--fresh`

4. **Clear User Feedback**
   - Color-coded output (green=success, yellow=warning, red=error, blue=info)
   - Progress indicators for long operations
   - Detailed status reporting
   - Helpful next-step suggestions

### Database Initialization Flow

```
start-dev.sh
    |
    ├─> Check Docker running
    ├─> Start DB + Backend containers
    ├─> Wait for DB ready (pg_isready)
    ├─> Count tables in public schema
    |
    ├─> If --fresh flag:
    │       └─> Call setup-db.sh --fresh
    │
    ├─> Else if table_count = 0:
    │       └─> Call setup-db.sh
    │
    └─> Else (tables exist):
            └─> Skip initialization
            └─> Continue to backend health check
            └─> Start frontend
```

### setup-db.sh Flow

```
setup-db.sh [--with-demo-data] [--fresh]
    |
    ├─> Parse arguments
    ├─> Check Docker running
    ├─> Check/Start DB container
    ├─> Wait for DB ready
    |
    ├─> If --fresh:
    │       └─> DROP SCHEMA public CASCADE
    │       └─> CREATE SCHEMA public
    │
    ├─> Run Alembic migrations
    │   └─> alembic upgrade head
    │
    ├─> If --with-demo-data:
    │       └─> Run init_users.py (full demo data)
    │
    └─> Else:
            └─> Run init_users_only.py (users only)
```

## Usage Examples

### First-Time Developer Setup

```bash
# Clone repository
git clone https://github.com/geodanchev/DomOS.git
cd DomOS/mvp1-cashier

# Just run start-dev.sh - everything is automatic!
./start-dev.sh

# Output:
# ✓ Docker is running
# 📦 Starting Database and Backend containers...
# ⏳ Waiting for database to be ready...
# ✓ Database is ready
# 🔍 Checking database initialization...
# ⚠ Database not initialized (no tables found)
#   Running initial database setup...
# [setup-db.sh runs automatically]
# ✅ Database setup completed successfully!
# ⏳ Waiting for backend to be ready...
# ✓ Backend is ready
# 🎨 Frontend: Starting Vite on http://localhost:5173
```

### Developer Wants Fresh Start

```bash
# Reset everything and start clean
./start-dev.sh --fresh

# Or manually reset database only
./setup-db.sh --fresh
```

### Developer Wants Full Demo Data

```bash
# Option 1: Manual setup with demo data
./setup-db.sh --with-demo-data

# Option 2: Fresh install with demo data
./setup-db.sh --fresh --with-demo-data

# Then start normally
./start-dev.sh
```

### Adding New Migration

```bash
# Developer creates new Alembic migration
cd backend
alembic revision -m "add new feature"
# Edit migration file
# ...

# Apply migration
./setup-db.sh
# Output:
# ✓ Database is ready
# 📊 Running database migrations...
# ✓ Database schema updated
# ✓ Users already exist (2 users found), skipping creation...
```

## Testing Checklist

- [x] `setup-db.sh` creates database schema from scratch
- [x] `setup-db.sh` creates users (admin, cecka)
- [x] `setup-db.sh --with-demo-data` loads full demo data
- [x] `setup-db.sh --fresh` drops all tables and recreates
- [x] `init_users_only.py` is idempotent (can run multiple times)
- [x] `init_users_only.py` skips if users exist
- [x] `start-dev.sh` detects empty database on first run
- [x] `start-dev.sh` auto-initializes database on first run
- [x] `start-dev.sh` skips initialization on subsequent runs
- [x] `start-dev.sh --fresh` resets database and recreates
- [x] Scripts work with backend container running
- [x] Scripts work without backend container (local execution)
- [x] Error handling works correctly
- [x] Color output displays properly
- [x] Scripts are executable (`chmod +x`)

## Benefits

### For New Developers
- **Zero configuration:** Just run `./start-dev.sh` and everything works
- **No manual steps:** Database initialization is automatic
- **Clear feedback:** Know exactly what's happening at each step
- **Safe defaults:** Users-only setup prevents data bloat during development

### For Experienced Developers
- **Fast iteration:** `--fresh` flag for quick resets
- **Flexible data:** Choose between minimal and full demo data
- **Scriptable:** All operations can be automated in CI/CD
- **Idempotent:** Safe to run repeatedly without side effects

### For CI/CD
- **Automated testing:** Scripts can run in CI environment
- **Reproducible:** Same initialization every time
- **No manual intervention:** Fully automated workflow

## Technical Notes

### Database Health Checks

Scripts use PostgreSQL's `pg_isready` command:
```bash
docker exec domos-db-dev pg_isready -U postgres -d domos_cashier
```

This is more reliable than simple port checks and ensures the database is actually ready to accept connections.

### Table Count Detection

To detect if database is initialized:
```bash
TABLE_COUNT=$(docker exec domos-db-dev psql -U postgres -d domos_cashier -t -c \
  "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" \
  2>/dev/null | tr -d ' ' || echo "0")
```

### Alembic Integration

Scripts support both Docker and local execution:
```bash
if docker ps --format '{{.Names}}