---
name: domos-remote-update
description: Update an existing DomOS deployment to the latest version with database backup and migrations. Use when the user asks to update DomOS, upgrade DomOS, pull latest changes, apply new version, sync remote deployment, or актуализирай/ъпдейтни DomOS (Bulgarian).
---

# DomOS Remote Update

This skill provides step-by-step instructions for safely updating an existing DomOS deployment on a remote Linux machine.

## Prerequisites

- DomOS already deployed via `domos-remote-deploy` skill
- SSH access to the remote machine
- GitHub PAT with repo access (stored as `GIT_PAT` in secrets)

## Important Notes

⚠️ **Always create a database backup before updating!**

⚠️ **SECRET_KEY changes will invalidate all existing JWT tokens** - users will need to log in again.

## Update Steps

### 1. Create Database Backup

**Critical step - do not skip!**

```bash
sshpass -p 'PASSWORD' ssh USER@IP 'cd ~/projects/DomOS/mvp1-cashier && echo "PASSWORD" | sudo -S docker compose exec -T db pg_dump -U postgres domos_cashier > backup_$(date +%Y%m%d_%H%M%S).sql && ls -la backup_*.sql'
```

Verify backup file was created and has reasonable size (not 0 bytes).

### 2. Pull Latest Changes from GitHub

First, check for local modifications:

```bash
sshpass -p 'PASSWORD' ssh USER@IP 'cd ~/projects/DomOS && git status'
```

If there are local changes (common: `tsconfig.json`), discard them:

```bash
sshpass -p 'PASSWORD' ssh USER@IP 'cd ~/projects/DomOS && git checkout -- .'
```

Then pull latest changes:

```bash
sshpass -p 'PASSWORD' ssh USER@IP 'cd ~/projects/DomOS && git pull origin main 2>&1'
```

### 3. Stop Current Containers

```bash
sshpass -p 'PASSWORD' ssh USER@IP 'cd ~/projects/DomOS/mvp1-cashier && echo "PASSWORD" | sudo -S docker compose down 2>&1'
```

### 4. Rebuild Docker Containers

Use `--no-cache` to ensure fresh build with all changes:

```bash
sshpass -p 'PASSWORD' ssh USER@IP 'cd ~/projects/DomOS/mvp1-cashier && echo "PASSWORD" | sudo -S docker compose build --no-cache 2>&1'
```

This step takes 1-3 minutes depending on network speed.

### 5. Start Database First

```bash
sshpass -p 'PASSWORD' ssh USER@IP 'cd ~/projects/DomOS/mvp1-cashier && echo "PASSWORD" | sudo -S docker compose up -d db && sleep 10 && echo "PASSWORD" | sudo -S docker compose ps'
```

Wait until `domos-db` shows `healthy` status.

### 6. Run Database Migrations

```bash
sshpass -p 'PASSWORD' ssh USER@IP 'cd ~/projects/DomOS/mvp1-cashier && echo "PASSWORD" | sudo -S docker compose run --rm backend alembic upgrade head 2>&1'
```

#### Handling SECRET_KEY Validation Error

If you see this error:
```
SECURITY ERROR: SECRET_KEY is set to a known weak/default value
```

Generate and set a secure SECRET_KEY:

```bash
# Generate secure key locally
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Update .env file on remote
sshpass -p 'PASSWORD' ssh USER@IP "cd ~/projects/DomOS/mvp1-cashier && sed -i 's|SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|' .env && grep SECRET_KEY .env"
```

Then retry the migration command.

### 7. Start All Services

```bash
sshpass -p 'PASSWORD' ssh USER@IP 'cd ~/projects/DomOS/mvp1-cashier && echo "PASSWORD" | sudo -S docker compose up -d && sleep 10 && echo "PASSWORD" | sudo -S docker compose ps'
```

Verify all three containers show healthy status:
- `domos-db` - healthy
- `domos-backend` - healthy  
- `domos-frontend` - running (health: starting is OK initially)

### 8. Verify ngrok Tunnel

Check if ngrok is still running:

```bash
sshpass -p 'PASSWORD' ssh USER@IP 'curl -s http://localhost:4040/api/tunnels'
```

If ngrok is not running (empty response or connection refused), restart it:

```bash
sshpass -p 'PASSWORD' ssh USER@IP 'pkill ngrok 2>/dev/null; nohup ~/ngrok http 3000 > /tmp/ngrok.log 2>&1 &'
```

Wait a few seconds and get the new URL:

```bash
sleep 5 && sshpass -p 'PASSWORD' ssh USER@IP 'curl -s http://localhost:4040/api/tunnels'
```

Extract `public_url` from the JSON response.

## Quick Update Script

For experienced users, here's a condensed all-in-one command sequence:

```bash
# Set variables
USER=gosh
IP=192.168.88.25
PASSWORD=1

# Execute update
sshpass -p "$PASSWORD" ssh $USER@$IP '
  cd ~/projects/DomOS/mvp1-cashier &&
  echo "'$PASSWORD'" | sudo -S docker compose exec -T db pg_dump -U postgres domos_cashier > backup_$(date +%Y%m%d_%H%M%S).sql &&
  cd ~/projects/DomOS &&
  git checkout -- . &&
  git pull origin main &&
  cd mvp1-cashier &&
  echo "'$PASSWORD'" | sudo -S docker compose down &&
  echo "'$PASSWORD'" | sudo -S docker compose build --no-cache &&
  echo "'$PASSWORD'" | sudo -S docker compose up -d db &&
  sleep 10 &&
  echo "'$PASSWORD'" | sudo -S docker compose run --rm backend alembic upgrade head &&
  echo "'$PASSWORD'" | sudo -S docker compose up -d &&
  echo "'$PASSWORD'" | sudo -S docker compose ps
'
```

## Rollback Procedure

If something goes wrong after update:

### 1. Restore from Backup

```bash
sshpass -p 'PASSWORD' ssh USER@IP 'cd ~/projects/DomOS/mvp1-cashier && cat backup_YYYYMMDD_HHMMSS.sql | echo "PASSWORD" | sudo -S docker compose exec -T db psql -U postgres domos_cashier'
```

### 2. Revert to Previous Git Commit

```bash
sshpass -p 'PASSWORD' ssh USER@IP 'cd ~/projects/DomOS && git log --oneline -5'
# Find the previous commit hash, then:
sshpass -p 'PASSWORD' ssh USER@IP 'cd ~/projects/DomOS && git checkout COMMIT_HASH'
```

### 3. Rebuild and Restart

```bash
sshpass -p 'PASSWORD' ssh USER@IP 'cd ~/projects/DomOS/mvp1-cashier && echo "PASSWORD" | sudo -S docker compose down && echo "PASSWORD" | sudo -S docker compose build --no-cache && echo "PASSWORD" | sudo -S docker compose up -d'
```

## Troubleshooting

### Migration Fails with Import Error

Usually indicates missing dependency or code error. Check logs:

```bash
sshpass -p 'PASSWORD' ssh USER@IP 'cd ~/projects/DomOS/mvp1-cashier && echo "PASSWORD" | sudo -S docker compose logs backend'
```

### Containers Won't Start

Check individual container logs:

```bash
sshpass -p 'PASSWORD' ssh USER@IP 'echo "PASSWORD" | sudo -S docker logs domos-backend'
sshpass -p 'PASSWORD' ssh USER@IP 'echo "PASSWORD" | sudo -S docker logs domos-frontend'
sshpass -p 'PASSWORD' ssh USER@IP 'echo "PASSWORD" | sudo -S docker logs domos-db'
```

### Port Conflict After Update

If frontend fails to start due to port conflict:

```bash
sshpass -p 'PASSWORD' ssh USER@IP 'echo "PASSWORD" | sudo -S lsof -i :3000'
```

Kill conflicting process or change port in `.env` file.

### ngrok URL Changed

ngrok free tier URLs change on restart. Check current URL:

```bash
sshpass -p 'PASSWORD' ssh USER@IP 'curl -s http://localhost:4040/api/tunnels | grep -o "https://[^\"]*"'
```

## Post-Update Checklist

- [ ] Database backup created and verified
- [ ] All containers showing healthy status
- [ ] ngrok tunnel active with public URL
- [ ] Application accessible via ngrok URL
- [ ] Login functionality works (if SECRET_KEY changed, existing sessions invalidated)
- [ ] Core functionality tested (view apartments, payments, etc.)
