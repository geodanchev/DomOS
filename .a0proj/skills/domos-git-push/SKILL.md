---
name: domos-git-push
description: Push DomOS project changes to GitHub. Use when the user asks to sync, push, or commit DomOS changes. Handles PAT token extraction, selective staging (excludes memory indices and backups), commit creation, and push to origin.
---

# DomOS Git Push

Automates the Git workflow for the DomOS project with proper file filtering and authentication.

## When to Use

- User says: "push", "sync git", "commit and push", "sync to github"
- User asks about git status in DomOS context
- After completing DomOS development work

## Workflow

### 1. Check Status

```bash
cd /a0/usr/projects/domos && git status
```

### 2. Identify Changes

Always exclude:
- `.a0proj/memory/*` files (local indices)
- `*.backup` files (database backups)
- Any temporary or cache files

Include everything else that is modified or new.

### 3. Stage Changes

```bash
# Add specific files/directories, NOT using git add -A blindly
git add <file1> <file2> <dir1>/

# If you accidentally staged unwanted files:
git reset .a0proj/memory/*
git reset **/*.backup
```

### 4. Create Commit

Use descriptive commit messages in this format:

```bash
git commit -m 'Category: Brief description

- Detail 1
- Detail 2
- Detail 3'
```

Categories: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`

### 5. Push with PAT

```bash
# Extract PAT from secrets
export GIT_PAT=$(cat /a0/usr/secrets.env | grep GIT_PAT | cut -d'=' -f2)

# Push to GitHub
git push https://${GIT_PAT}@github.com/geodanchev/DomOS.git main
```

## Full Example Script

```bash
cd /a0/usr/projects/domos

# Check what changed
git status

# Stage relevant files (example)
git add mvp1-cashier/backend/init_db.py \
        mvp1-cashier/backend/reset_db.py \
        mvp1-cashier/frontend/vite.config.ts

# Commit with message
git commit -m 'chore: Update database initialization and dev config

- Add reset_db.py utility
- Update init_db.py with new schema
- Configure Vite for dev environment'

# Extract PAT and push
export GIT_PAT=$(cat /a0/usr/secrets.env | grep GIT_PAT | cut -d'=' -f2)
git push https://${GIT_PAT}@github.com/geodanchev/DomOS.git main
```

## Error Handling

### PAT Not Found

If PAT extraction fails:
1. Check `/a0/usr/secrets.env` exists
2. Verify format: `GIT_PAT=ghp_...`
3. Token must have `repo` scope with write permissions

### Push Rejected

- Pull first if behind: `git pull origin main`
- Resolve conflicts if any
- Then retry push

### Nothing to Commit

If git status shows only `.a0proj/memory/*` changes:
- These are local indices, ignore them
- Report to user: "No project changes to commit"

## Key Rules

1. **Never commit** `.a0proj/memory/*` files
2. **Never commit** `*.backup` files
3. **Always** extract PAT from secrets before push
4. **Always** use descriptive commit messages
5. **Check status** before starting workflow
6. **Report results** clearly to user after push

## Integration

This skill is project-scoped. Load it automatically when:
- Working directory is `/a0/usr/projects/domos`
- User mentions git/push/sync in DomOS context
