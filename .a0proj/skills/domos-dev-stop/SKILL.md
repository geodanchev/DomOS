# domos-dev-stop

Stop the DomOS MVP1 Cashier application running in development mode.

## Trigger Phrases
- "спри приложението" (stop the application)
- "стоп" (stop)
- "stop domos"
- "stop the cashier app"
- "kill dev servers"

## Stop Commands

### Stop All DomOS Services
```bash
# Kill backend (uvicorn)
pkill -f "uvicorn app.main:app" 2>/dev/null && echo "Backend stopped" || echo "Backend was not running"

# Kill frontend (vite)
pkill -f "vite" 2>/dev/null && echo "Frontend stopped" || echo "Frontend was not running"
```

### Stop by Port (Alternative)
```bash
# Stop backend on port 8000
kill $(lsof -t -i:8000) 2>/dev/null && echo "Port 8000 freed" || echo "Port 8000 was free"

# Stop frontend on port 5173
kill $(lsof -t -i:5173) 2>/dev/null && echo "Port 5173 freed" || echo "Port 5173 was free"
```

## Verification

After stopping, verify services are down:
```bash
lsof -i :8000 2>/dev/null || echo "✓ Port 8000 free"
lsof -i :5173 2>/dev/null || echo "✓ Port 5173 free"
```

## Related Skills
- `domos-dev-start` - Start the development environment
- `domos-git-push` - Push changes to GitHub
