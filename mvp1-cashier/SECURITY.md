# Security Documentation - DomOS Cashier MVP

## Overview

This document describes the security measures implemented in the DomOS Cashier MVP application.

## Security Fixes Implemented (June 2026)

### 1. ✅ Protected /register Endpoint (Critical)

**File:** `backend/app/api/auth.py`

**Problem:** The `/register` endpoint was open to anyone, allowing unauthorized user creation including admin accounts.

**Solution:** Added `require_admin` dependency to the `/register` endpoint. Only authenticated administrators can now create new users.

```python
@router.post("/register", ...)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_admin),  # SECURITY: Admin-only
):
```

### 2. ✅ SECRET_KEY Validation (Critical)

**File:** `backend/app/core/config.py`

**Problem:** Default weak SECRET_KEY could be used in production, allowing JWT token forgery.

**Solution:** Added Pydantic validator that checks SECRET_KEY in production mode:
- Rejects known weak/default values
- Requires minimum 32 characters
- Only enforced when `DEBUG=false`

```python
@field_validator('SECRET_KEY')
@classmethod
def validate_secret_key(cls, v: str) -> str:
    # Validates SECRET_KEY security requirements in production
```

**Generate a secure key:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. ✅ Removed Hardcoded Credentials (Critical)

**File:** `backend/init_users.py`

**Problem:** Demo user passwords (admin123, 1234) were hardcoded in source code.

**Solution:** Passwords are now read from environment variables:
- `DEMO_ADMIN_PASSWORD`
- `DEMO_CASHIER_PASSWORD`

In production mode, missing passwords prevent user creation.

### 4. ✅ Environment-Based Demo Data Control (Critical)

**File:** `backend/app/core/config.py`, `backend/init_users.py`

**Problem:** Demo users were always created, even in production.

**Solution:** Added `INIT_DEMO_DATA` environment variable:
- `true` (default in development): Creates demo users
- `false` (required in production): Skips demo user creation entirely

---

## Production Deployment Checklist

Before deploying to production, ensure:

- [ ] `DEBUG=false`
- [ ] `SECRET_KEY` is unique, random, and at least 32 characters
- [ ] `INIT_DEMO_DATA=false`
- [ ] Database uses PostgreSQL with secure credentials
- [ ] CORS origins are restricted to your production domain(s)
- [ ] `.env.production` is NOT committed to version control
- [ ] Initial admin user created via secure database migration or manual insert
- [ ] HTTPS is enabled
- [ ] Rate limiting is configured

---

## Environment Files

| File | Purpose | Commit to Git? |
|------|---------|----------------|
| `.env` | Development configuration | ⚠️ Only with non-sensitive defaults |
| `.env.production` | Production configuration | ❌ **NEVER** |
| `.env.production.example` | Production template | ✅ Yes |

---

## Authentication Flow

1. User submits username/password to `/api/auth/login`
2. Server validates credentials against bcrypt hash
3. Server issues JWT token (HS256, configurable expiry)
4. Client includes token in `Authorization: Bearer <token>` header
5. Protected endpoints validate token and check user role

---

## Role-Based Access Control

| Role | Capabilities |
|------|--------------|
| `admin` | Full access, can create/manage users |
| `cashier` | Can record payments, view reports |
| `viewer` | Read-only access |

---

## Security Dependencies

- **bcrypt**: Password hashing
- **python-jose**: JWT token handling
- **pydantic**: Configuration validation

---

## Reporting Security Issues

If you discover a security vulnerability, please report it privately to the development team.

---

## Audit Log

All critical actions are logged in the `audit_log` table with:
- User ID
- Action type
- Entity affected
- Timestamp
- IP address (when available)

---

*Last updated: June 2026*
