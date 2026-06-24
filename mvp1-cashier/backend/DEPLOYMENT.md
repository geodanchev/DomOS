# DomOS Cashier MVP - Deployment Guide

## Overview

This guide covers development and production deployment workflows for the DomOS Cashier backend.

## Quick Start

### Development Environment

```bash
# Use standard entrypoint.sh for development
docker-compose up
```

### Production Environment

```bash
# 1. Create production environment file
cp .env.production.example .env.production

# 2. Edit .env.production and set required values:
# - DATABASE_URL (with strong password)
# - SECRET_KEY (generate with: openssl rand -hex 32)
# - ENVIRONMENT=production
# - CORS_ORIGINS (your production domain)

# 3. Deploy with production entrypoint
docker-compose -f docker-compose.prod.yml up -d
```

## Entrypoint Scripts

### `entrypoint.sh` - Development/Standard Mode

**Features:**
- Automatic database detection
- Runs migrations on first run
- Initializes users automatically on empty database
- Optional seed data via `INIT_DB=true` flag
- Safe for development and staging environments

**Workflow:**
```
1. Wait for database connection
2. Check if database is empty (no alembic_version table)
3. If empty:
   - Run migrations (alembic upgrade head)
   - Initialize users (init_users.py)
   - Optionally run seed data if INIT_DB=true
4. If not empty:
   - Run migrations only (safe idempotent operation)
5. Start uvicorn server
```

### `entrypoint.prod.sh` - Production Mode

**Features:**
- Strict environment variable validation
- Production safety checks (blocks INIT_DB=true)
- Health checks before starting server
- Production-optimized uvicorn configuration
- Detailed startup logging

**Workflow:**
```
1. Validate required environment variables
2. Check production safety flags
3. Wait for database connection
4. Check database state
5. If empty (first deployment):
   - Run migrations
   - Initialize production users
   - Display post-deployment checklist
6. If not empty:
   - Run migrations only
7. Perform application health check
8. Start production uvicorn server
```

**Production Safety Features:**
- ❌ Blocks `INIT_DB=true` (prevents accidental demo data in production)
- ✅ Validates `SECRET_KEY` length (min 32 characters)
- ✅ Checks `ENVIRONMENT=production`
- ⚠️ Warns if `DEBUG=true` in production
- 🏥 Health check imports core modules before starting server

## Database Initialization

### First Run Behavior

**Development (`entrypoint.sh`):**
```bash
# Automatic on first run:
- Migrations: ✅ Automatic
- User initialization: ✅ Automatic
- Seed data: ⚠️ Only if INIT_DB=true
```

**Production (`entrypoint.prod.sh`):**
```bash
# Automatic on first deployment:
- Migrations: ✅ Automatic
- User initialization: ✅ Automatic
- Seed data: ❌ Never (blocked by safety check)
```

### Migration Scripts

```bash
# Create new migration
./create-migration.sh "description"

# Manual migration (inside container)
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

### User Initialization Scripts

- `init_users.py` - Initialize default admin users (used by both entrypoints)
- `init_users_only.py` - Standalone script for manual user initialization
- `init_db.py` - Initialize seed/demo data (development only)

## Environment Variables

### Required (Production)

| Variable | Description | Example |
|----------|-------------|----------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `SECRET_KEY` | JWT signing key (32+ chars) | `openssl rand -hex 32` |
| `ENVIRONMENT` | Environment identifier | `production` |

### Optional

| Variable | Description | Default |
|----------|-------------|----------|
| `INIT_DB` | Enable seed data (dev only) | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `DEBUG` | Debug mode | `false` |
| `CORS_ORIGINS` | Allowed CORS origins | `*` (dev) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT expiration | `60` |

## Production Deployment Checklist

### Pre-Deployment

- [ ] Copy `.env.production.example` to `.env.production`
- [ ] Generate strong `SECRET_KEY`: `openssl rand -hex 32`
- [ ] Set strong `DATABASE_URL` password
- [ ] Configure `CORS_ORIGINS` with actual domain(s)
- [ ] Set `ENVIRONMENT=production`
- [ ] Set `LOG_LEVEL=INFO` or `WARNING`
- [ ] Set `DEBUG=false`
- [ ] Verify `INIT_DB` is NOT set to `true`
- [ ] Test database connection
- [ ] Review all security settings
- [ ] Configure automated backups
- [ ] Set up monitoring and alerting

### Post-Deployment

- [ ] Login with default admin credentials
- [ ] **IMMEDIATELY change all default passwords**
- [ ] Create additional admin users
- [ ] Configure building-specific settings
- [ ] Test critical workflows:
  - [ ] Payments
  - [ ] Obligations
  - [ ] Reports
  - [ ] Receipt generation
- [ ] Verify backup procedures
- [ ] Set up monitoring dashboards
- [ ] Document deployment date and version

## Database Backups

### Manual Backup

```bash
# Backup database
./backup-db.sh

# Restore from backup
./restore-db.sh <backup-file>
```

### Automated Backups (Recommended for Production)

Configure in `.env.production`:

```bash
BACKUP_SCHEDULE="0 2 * * *"  # Daily at 2:00 AM
BACKUP_RETENTION_DAYS=30
BACKUP_PATH=/var/backups/domos
```

## Monitoring and Logging

### Log Levels

- `DEBUG` - Detailed diagnostic information (development only)
- `INFO` - General informational messages (recommended for production)
- `WARNING` - Warning messages for non-critical issues
- `ERROR` - Error messages for failures
- `CRITICAL` - Critical failures requiring immediate attention

### Health Check Endpoint

```bash
# Check application health
curl http://localhost:8000/health

# Expected response
{"status": "healthy", "database": "connected"}
```

## Troubleshooting

### Database Connection Issues

**Symptom:** `Database connection failed after 30 attempts`

**Solutions:**
1. Verify `DATABASE_URL` is correct
2. Check database server is running
3. Verify network connectivity
4. Check database user permissions

### Missing Environment Variables

**Symptom:** `CRITICAL ERROR: Missing required environment variables`

**Solutions:**
1. Ensure `.env.production` file exists
2. Verify all required variables are set
3. Check for typos in variable names
4. Ensure no extra whitespace around values

### Migration Failures

**Symptom:** `ERROR: No alembic directory found`

**Solutions:**
1. Verify `alembic/` directory exists
2. Check alembic.ini configuration
3. Ensure running from correct directory

### Health Check Failures

**Symptom:** `Application health check failed - cannot import core modules`

**Solutions:**
1. Verify all dependencies are installed
2. Check for Python syntax errors
3. Review recent code changes
4. Check application logs for import errors

### Production Safety Blocks

**Symptom:** `CRITICAL ERROR: INIT_DB=true is not allowed in production!`

**Solution:** Remove or set `INIT_DB=false` in `.env.production`

## Security Best Practices

1. **Never commit `.env.production` to version control**
2. **Rotate `SECRET_KEY` periodically** (every 90 days recommended)
3. **Use strong database passwords** (20+ characters, mixed case, numbers, symbols)
4. **Restrict database user permissions** (only necessary grants)
5. **Enable SSL/TLS for database connections** (use `sslmode=require` in `DATABASE_URL`)
6. **Configure CORS properly** (never use `*` in production)
7. **Keep dependencies updated** (monitor for security patches)
8. **Enable automated backups** (test restore procedures regularly)
9. **Monitor logs for suspicious activity**
10. **Implement rate limiting** (at reverse proxy level)

## Docker Configuration

### Development

```yaml
# docker-compose.yml
services:
  backend:
    entrypoint: ["/app/entrypoint.sh"]
    environment:
      - INIT_DB=true  # Optional seed data
```

### Production

```yaml
# docker-compose.prod.yml
services:
  backend:
    entrypoint: ["/app/entrypoint.prod.sh"]
    environment:
      - ENVIRONMENT=production
      # INIT_DB must not be set
```

## Support

For issues or questions:
1. Check this documentation
2. Review application logs
3. Consult project README.md
4. Contact development team

---

**Last Updated:** 2026-06-24  
**Version:** MVP 1.0
