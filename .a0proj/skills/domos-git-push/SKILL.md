---
name: domos-git-push
description: Push DomOS project changes to GitHub. Use when the user asks to sync, push, or commit DomOS changes. Handles PAT token selection (standard vs workflow scope), selective staging (excludes memory indices and backups), commit creation, and push to origin with proper authentication.
---

# DomOS Git Push

Automates the Git workflow for the DomOS project with proper file filtering, authentication, and workflow scope handling.

## When to Use

- User says: "push", "sync git", "commit and push", "sync to github"
- User asks about git status in DomOS context
- After completing DomOS development work
- After creating or modifying CI/CD pipeline files

## Important: GitHub Workflow Scope Requirement

### Two Types of Changes

**Standard Changes** (use `GIT_PAT`):
- Application code (backend, frontend)
- Documentation (README, docs)
- Configuration files
- Database migrations
- Scripts and utilities

**Workflow Changes** (use `GIT_PAT_WORKFLOW`):
- Any file in `.github/workflows/` directory
- GitHub Actions workflow files (*.yml, *.yaml)
- CI/CD pipeline configurations

### Why Two Tokens?

GitHub requires special `workflow` scope permission to create or modify GitHub Actions workflows. This is a security feature to prevent unauthorized workflow modifications.

**Error you'll see if using wrong token:**
```
remote: refusing to allow a Personal Access Token to create or update workflow 
`.github/workflows/ci.yml` without `workflow` scope
error: failed to push some refs
```

## Token Setup

### Standard Token (GIT_PAT)

**When to create:** For regular code changes

**Scopes required:**
- ✅ `repo` (Full control of private repositories)

**Steps:**
1. Go to: https://github.com/settings/tokens/new
2. Note: `Agent Zero - DomOS (Write Access)`
3. Expiration: 90 days or custom
4. Select scope: `repo`
5. Generate and copy token
6. Store in secrets.env file with key `GIT_PAT`

### Workflow Token (GIT_PAT_WORKFLOW)

**When to create:** For CI/CD and workflow file changes

**Scopes required:**
- ✅ `repo` (Full control of private repositories)
- ✅ `workflow` (Update GitHub Action workflows)

**Steps:**
1. Go to: https://github.com/settings/tokens/new
2. Note: `Agent Zero - DomOS (Full Access with Workflow)`
3. Expiration: 90 days or custom
4. Select scopes: `repo` AND `workflow`
5. Generate and copy token
6. Store in secrets.env file with key `GIT_PAT_WORKFLOW`

## Workflow

### 1. Check Status

```bash
cd /a0/usr/projects/domos && git status
```

### 2. Identify Changes

**Always exclude:**
- `.a0proj/memory/*` files (local indices)
- `*.backup` files (database backups)
- Any temporary or cache files

**Include everything else** that is modified or new.

**Check for workflow files:**
```bash
git status | grep -E '\.github/workflows/'
```

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

**Categories:** `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `ci`

### 5. Push with Correct PAT Token

**Decision Logic:**

```
IF changes include .github/workflows/* files:
  → Use secret replacement for GIT_PAT_WORKFLOW
ELSE:
  → Use secret replacement for GIT_PAT
```

**Command Template:**

For standard changes (no workflow files):
```bash
# Use the secret replacement syntax with GIT_PAT
git push https://$TOKEN@github.com/geodanchev/DomOS.git <branch-name>
```

For workflow changes (includes .github/workflows/ files):
```bash
# Use the secret replacement syntax with GIT_PAT_WORKFLOW
git push https://$TOKEN@github.com/geodanchev/DomOS.git <branch-name>
```

**Note:** In actual execution, replace `$TOKEN` with the appropriate secret replacement syntax using double section signs.

## Full Example Scripts

### Example 1: Standard Code Changes

```bash
cd /a0/usr/projects/domos

# Check what changed
git status

# Stage relevant files (example)
git add mvp1-cashier/backend/app/models/user.py \
        mvp1-cashier/frontend/src/pages/Dashboard.tsx \
        README.md

# Commit with message
git commit -m 'feat: Add user profile page and update docs

- Add user model fields
- Create dashboard profile section
- Update README with new features'

# Push with standard token (GIT_PAT)
# Replace $TOKEN with secret replacement for GIT_PAT
git push https://$TOKEN@github.com/geodanchev/DomOS.git main
```

### Example 2: CI/CD Workflow Changes

```bash
cd /a0/usr/projects/domos

# Check what changed
git status

# Stage CI files and related changes
git add .github/workflows/ci.yml \
        CI.md \
        mvp1-cashier/frontend/package.json

# Commit with message
git commit -m 'ci: Add GitHub Actions pipeline with automated testing

- Create workflow for PR testing
- Include backend pytest and frontend vitest
- Add linting checks
- Add CI documentation'

# Push with workflow token (GIT_PAT_WORKFLOW) - IMPORTANT!
# Replace $TOKEN with secret replacement for GIT_PAT_WORKFLOW
git push https://$TOKEN@github.com/geodanchev/DomOS.git main
```

### Example 3: Mixed Changes (Workflow + Code)

```bash
cd /a0/usr/projects/domos

# Check what changed
git status

# Stage all relevant files including workflow
git add .github/workflows/deploy.yml \
        mvp1-cashier/backend/app/main.py \
        mvp1-cashier/frontend/src/App.tsx

# Commit
git commit -m 'feat: Add deployment workflow and app updates

- Create automated deployment pipeline
- Update backend API endpoints
- Improve frontend error handling'

# Use workflow token because .github/workflows/ is included
# Replace $TOKEN with secret replacement for GIT_PAT_WORKFLOW
git push https://$TOKEN@github.com/geodanchev/DomOS.git main
```

## Error Handling

### Workflow Scope Error

**Error message:**
```
remote: refusing to allow a Personal Access Token to create or update workflow 
`.github/workflows/ci.yml` without `workflow` scope
error: failed to push some refs
```

**Solution:**
1. Check if you have `GIT_PAT_WORKFLOW` configured in secrets
2. If not, create new PAT with `workflow` scope (see Token Setup above)
3. Retry push using GIT_PAT_WORKFLOW secret replacement

### PAT Not Found

**If token is missing from secrets:**
1. Check secrets.env file exists
2. Verify token is stored with correct key: `GIT_PAT` or `GIT_PAT_WORKFLOW`
3. Ensure proper permissions on secrets.env file
4. Create token if missing (see Token Setup)

### Push Rejected (Behind Remote)

**Error:** `Updates were rejected because the tip of your current branch is behind`

**Solution:**
```bash
# Pull latest changes first
git pull origin <branch-name>

# Resolve conflicts if any
# Then retry push
git push https://$TOKEN@github.com/geodanchev/DomOS.git <branch-name>
```

### Nothing to Commit

If `git status` shows only `.a0proj/memory/*` or `*.backup` changes:
- These are local files and should be ignored
- Report to user: "No project changes to commit"

## Quick Decision Tree

```
Are you pushing changes to .github/workflows/ ?
│
├─ YES → Use GIT_PAT_WORKFLOW secret replacement
│
└─ NO  → Use GIT_PAT secret replacement
```

## Key Rules

1. **Never commit** `.a0proj/memory/*` files
2. **Never commit** `*.backup` files
3. **Always check** if `.github/workflows/` files are included in changes
4. **Use GIT_PAT_WORKFLOW** for any workflow-related changes
5. **Use GIT_PAT** for standard code changes
6. **Always** use the secret replacement syntax (with double section signs) for authentication
7. **Always** use descriptive commit messages
8. **Check status** before starting workflow
9. **Report results** clearly to user after push

## Token Security

- Never expose token values in logs or output
- Use secret replacement syntax always (double section signs followed by secret(TOKEN_NAME))
- Store tokens in secrets.env file only
- Keep workflow token separate from standard token
- Regenerate tokens if compromised
- Use appropriate expiration dates (90 days recommended)

## Integration

This skill is project-scoped. Load it automatically when:
- Working directory is `/a0/usr/projects/domos`
- User mentions git/push/sync in DomOS context
- User asks about CI/CD or workflow setup
