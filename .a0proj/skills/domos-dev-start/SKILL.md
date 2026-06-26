# domos-dev-start

Start the DomOS MVP1 Cashier application in development mode.

## Trigger Phrases
- "пусни приложението" (start the application)
- "стартирай dev" (start dev)
- "run domos"
- "start domos dev"
- "start the cashier app"
- "run mvp1 cashier"

## Prerequisites
- Backend virtual environment exists at `/a0/usr/projects/domos/mvp1-cashier/backend/venv`
- Frontend dependencies installed via npm
- No Docker required (runs directly with Python/Node)

## Environment Analysis

This skill handles running the application **without Docker**, which is necessary when:
- Running inside Agent Zero container (no docker-in-docker)
- Quick local development without container overhead
- Direct debugging with hot-reload

## Startup Sequence

### Step 1: Check for running processes
```bash
# Check if backend is already running on port 8000
lsof -i :8000 2>/dev/null || echo "Port 8000 free"

# Check if frontend is already running on port 5173  
lsof -i :5173 2>/dev/null || echo "Port 5173 free"
```

### Step 2: Start Backend (FastAPI with Uvicorn)
```bash
cd /a0/usr/projects/domos/mvp1-cashier/backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
```

**Expected output:**
- "Uvicorn running on http://0.0.0.0:8000"
- "Started reloader process"
- "Application startup complete"
- Scheduler logs for monthly obligations job

### Step 3: Start Frontend (Vite Dev Server)
```bash
cd /a0/usr/projects/domos/mvp1-cashier/frontend
npm run dev -- --host 0.0.0.0 --port 5173 &
```

**Expected output:**
- "VITE ready"
- "Local: http://localhost:5173/"
- "Network: http://172.x.x.x:5173/"

## Service URLs

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:5173 | React UI |
| Backend API | http://localhost:8000 | FastAPI REST API |
| API Docs | http://localhost:8000/docs | Swagger/OpenAPI |
| Health Check | http://localhost:8000/health | Service health |

## Default Users

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | ADMIN |
| cashier | cashier123 | CASHIER |
| viewer | viewer123 | VIEWER |

## Stopping Services

```bash
# Find and kill backend
pkill -f "uvicorn app.main:app"

# Find and kill frontend
pkill -f "vite"

# Or kill by port
kill $(lsof -t -i:8000) 2>/dev/null
kill $(lsof -t -i:5173) 2>/dev/null
```

## Troubleshooting

### Port already in use
```bash
# Check what's using the port
lsof -i :8000
lsof -i :5173

# Kill the process
kill -9 <PID>
```

### Backend won't start
1. Check venv exists: `ls /a0/usr/projects/domos/mvp1-cashier/backend/venv`
2. Check dependencies: `pip list | grep uvicorn`
3. Check database: `ls /a0/usr/projects/domos/mvp1-cashier/backend/domos_cashier.db`

### Frontend won't start
1. Check node_modules: `ls /a0/usr/projects/domos/mvp1-cashier/frontend/node_modules`
2. Reinstall if needed: `cd frontend && npm install`

## Session Management

Use separate terminal sessions for each service:
- Session 0: Backend (uvicorn)
- Session 1: Frontend (vite)

This allows independent monitoring and restart of each service.

## Related Skills
- `domos-git-push` - Push changes to GitHub
- `domos-dev-deploy` - Deploy to production
