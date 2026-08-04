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

## Feature Branch Strategy for Experiments

### Why Use Feature Branches?

When trying new approaches, implementations, or experiments:
- Create a **new branch** for each attempt
- If the approach fails or causes problems → **simply delete the branch**
- No need to track what was changed or perform complex rollbacks
- Clean slate: return to parent branch and start fresh

### Branch Hierarchy

Branches can be nested - you don't always start from `main`:

```
main
└── feature/user-auth          ← working feature (stable)
    ├── experiment/oauth-google   ← try approach 1
    ├── experiment/oauth-github   ← try approach 2 (if 1 failed)
    └── experiment/jwt-tokens     ← try approach 3 (if 2 failed)
```

**Key insight:** When you have a working feature branch, create experiment branches FROM that feature branch, not from main.

### Workflow

```bash
# 1. You're on a working feature branch
git checkout feature/user-auth

# 2. Before experimenting - CHECK PREVIOUS ATTEMPTS
cat .experiments/user-auth.md  # See what was already tried

# 3. Create experiment branch FROM current branch
git checkout -b experiment/oauth-google

# 4. Work on the experiment
# ... make changes, commits ...

# 5a. If experiment succeeds:
git checkout feature/user-auth
git merge experiment/oauth-google
git branch -d experiment/oauth-google
# Update experiments log with success

# 5b. If experiment fails - CLEAN ROLLBACK:
# First, document WHY it failed
echo "## experiment/oauth-google - FAILED" >> .experiments/user-auth.md
echo "Date: $(date)" >> .experiments/user-auth.md
echo "Idea: Use Google OAuth for authentication" >> .experiments/user-auth.md
echo "Why failed: Rate limits too restrictive for our use case" >> .experiments/user-auth.md
echo "" >> .experiments/user-auth.md

# Then delete the branch
git checkout feature/user-auth
git branch -D experiment/oauth-google

# Start next experiment
git checkout -b experiment/oauth-github
```

### Experiment Tracking

Create `.experiments/` directory in project root to track failed experiments:

```
.experiments/
├── user-auth.md           ← experiments for user-auth feature
├── payment-integration.md ← experiments for payments
└── database-schema.md     ← experiments for DB changes
```

**Template for experiment log:**

```markdown
# Experiments: [Feature Name]

## experiment/approach-name - STATUS
- **Date:** YYYY-MM-DD
- **Idea:** Brief description of the approach
- **Why failed/succeeded:** Explanation
- **Lessons learned:** What to avoid or remember

---
```

### Before Starting New Experiment

**ALWAYS check existing experiments first:**

```bash
# 1. List all branches to see current state
git branch -a

# 2. Check experiment history for this feature
cat .experiments/<feature-name>.md

# 3. See branch descriptions (if set)
git config --get-regexp 'branch\..*\.description'

# 4. Identify parent branch (where to return on failure)
git log --oneline --graph -10
```

### Branch Naming Conventions

| Prefix | Purpose | Example |
|--------|---------|----------|
| `experiment/` | Testing new approaches | `experiment/new-auth-flow` |
| `feature/` | Confirmed new features | `feature/user-profile` |
| `fix/` | Bug fixes | `fix/login-redirect` |
| `refactor/` | Code restructuring | `refactor/api-cleanup` |
| `chore/` | Maintenance tasks | `chore/update-deps` |

### Benefits

1. **No cognitive load** - Don't track what was changed
2. **Zero risk** - Parent branch stays clean
3. **Easy rollback** - Delete branch = complete undo
4. **Parallel experiments** - Multiple branches for different approaches
5. **Clean history** - Failed experiments don't pollute stable branches
6. **Documented failures** - Know what was tried and why it failed
7. **No repeated mistakes** - Check history before trying same approach

### When to Create a New Branch

- Trying a new library or approach
- Major refactoring
- Experimental feature implementation
- Any work where rollback might be needed
- When unsure if the approach will work
- **Upgrading or changing existing working code**

### Quick Decision

```
Is this work experimental or risky?
│
├─ YES → 1. Check .experiments/ for previous attempts
│        2. Create new branch from CURRENT branch
│           git checkout -b experiment/description
│        3. If fails: document reason, delete branch
│
└─ NO  → Continue on current branch (small safe changes)
```

### Git Commands Reference

```bash
# See all branches and current position
git branch -a

# Create experiment from current branch
git checkout -b experiment/name

# Return to parent branch after failure
git checkout <parent-branch>

# Force delete failed experiment
git branch -D experiment/name

# See branch hierarchy
git log --oneline --graph --all -20

# Set branch description (optional)
git config branch.experiment/name.description "Testing X approach"
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
