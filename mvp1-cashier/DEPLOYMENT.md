# DomOS Cashier MVP - Production Deployment Guide

## Overview

This guide covers complete production deployment of DomOS Cashier MVP using Docker Compose with:
- **Traefik** reverse proxy with automatic HTTPS (Let's Encrypt)
- **PostgreSQL** database with persistent storage
- **FastAPI** backend with health checks
- **React/Nginx** frontend with security headers
- **Rate limiting** for API protection
- **Comprehensive logging** for monitoring and debugging

---

## Prerequisites

### Server Requirements
- Linux server (Ubuntu 20.04+ recommended)
- Docker 24.0+
- Docker Compose v2+
- Minimum 2GB RAM, 20GB disk
- Ports 80 and 443 open

### Domain Setup
1. Register a domain name
2. Point DNS A record to your server's IP address
3. Wait for DNS propagation (5-30 minutes)

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/geodanchev/DomOS.git
cd DomOS/mvp1-cashier

# 2. Create production environment file
cp .env.production.example .env.production

# 3. Edit configuration
nano .env.production

# 4. Deploy
docker compose -f docker-compose.prod.yml --env-file .env.production up -d

# 5. Check status
docker compose -f docker-compose.prod.yml ps
```

---

## Environment Configuration

### Required Variables

Create `.env.production` with the following required settings:

```bash
# ===========================================
# REQUIRED - Domain and SSL
# ===========================================
DOMAIN=yourdomain.com
ACME_EMAIL=admin@yourdomain.com

# ===========================================
# REQUIRED - Security
# ===========================================
# Generate with: openssl rand -hex 32
SECRET_KEY=your-super-secret-key-min-32-characters

# Generate with: openssl rand -base64 32
POSTGRES_PASSWORD=your-secure-database-password

# Generate with: htpasswd -nb admin yourpassword
TRAEFIK_DASHBOARD_AUTH=admin:$apr1$xyz...
```

### Optional Variables

```bash
# ===========================================
# Database Configuration
# ===========================================
POSTGRES_USER=postgres           # Default: postgres
POSTGRES_DB=domos_cashier        # Default: domos_cashier

# ===========================================
# Application Settings
# ===========================================
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # Default: 1440 (24 hours)

# ===========================================
# Rate Limiting Configuration
# ===========================================
# General API endpoints
RATE_LIMIT_API_AVG=100            # Requests per period (default: 100)
RATE_LIMIT_API_BURST=50           # Burst allowance (default: 50)
RATE_LIMIT_API_PERIOD=1m          # Time period (default: 1m)

# Authentication endpoints (stricter limits)
RATE_LIMIT_AUTH_AVG=5             # Requests per period (default: 5)
RATE_LIMIT_AUTH_BURST=10          # Burst allowance (default: 10)
RATE_LIMIT_AUTH_PERIOD=1m         # Time period (default: 1m)

# IP detection depth for proxies
RATE_LIMIT_IP_DEPTH=1             # X-Forwarded-For depth (default: 1)

# ===========================================
# Logging Configuration
# ===========================================
TRAEFIK_LOG_LEVEL=INFO            # DEBUG, INFO, WARN, ERROR
```

---

## Rate Limiting

### Configuration

Rate limiting protects your API from abuse and brute-force attacks.

| Endpoint Type | Default Rate | Burst | Purpose |
|---------------|--------------|-------|----------|
| `/api/*` | 100/min | 50 | General API protection |
| `/api/auth/*` | 5/min | 10 | Brute-force prevention |
| `/health` | Unlimited | - | Health checks |

### Tuning Guidelines

**High Traffic Sites:**
```bash
RATE_LIMIT_API_AVG=500
RATE_LIMIT_API_BURST=200
```

**Extra Security:**
```bash
RATE_LIMIT_AUTH_AVG=3
RATE_LIMIT_AUTH_BURST=5
```

**Behind Multiple Proxies:**
```bash
# If behind Cloudflare + Load Balancer
RATE_LIMIT_IP_DEPTH=2
```

### Rate Limit Response

When limits are exceeded, clients receive:
- **HTTP 429** Too Many Requests
- **Retry-After** header with wait time in seconds

---

## Logging

### Log Locations

| Log Type | Location | Format |
|----------|----------|--------|
| Traefik Access | `traefik_logs` volume | JSON |
| Traefik System | Docker logs | JSON |
| Backend | Docker logs | Text |
| PostgreSQL | Docker logs | Text |

### Viewing Logs

```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs -f traefik
docker compose -f docker-compose.prod.yml logs -f backend

# Traefik access logs (rate limit events included)
docker exec domos-traefik cat /var/log/traefik/access.log | tail -100

# Filter rate-limited requests (HTTP 429)
docker exec domos-traefik cat /var/log/traefik/access.log | jq 'select(.DownstreamStatus == 429)'
```

### Log Format (JSON)

Each access log entry includes:
```json
{
  "ClientAddr": "192.168.1.100:54321",
  "ClientHost": "192.168.1.100",
  "DownstreamStatus": 429,
  "Duration": 1234567,
  "RequestMethod": "POST",
  "RequestPath": "/api/auth/login",
  "RouterName": "backend-auth@docker",
  "StartUTC": "2026-06-25T12:00:00.000000000Z",
  "request_User-Agent": "Mozilla/5.0...",
  "request_X-Forwarded-For": "203.0.113.50",
  "request_X-Real-Ip": "203.0.113.50"
}
```

### Monitoring Rate Limits

```bash
# Count 429 responses in last hour
docker exec domos-traefik cat /var/log/traefik/access.log | \
  jq -r 'select(.DownstreamStatus == 429) | .StartUTC' | \
  grep "$(date -u +%Y-%m-%dT%H)" | wc -l

# Top IPs hitting rate limits
docker exec domos-traefik cat /var/log/traefik/access.log | \
  jq -r 'select(.DownstreamStatus == 429) | .ClientHost' | \
  sort | uniq -c | sort -rn | head -10

# Rate limit events by endpoint
docker exec domos-traefik cat /var/log/traefik/access.log | \
  jq -r 'select(.DownstreamStatus == 429) | .RequestPath' | \
  sort | uniq -c | sort -rn
```

---

## Deployment Commands

### Initial Deployment

```bash
# Start all services
docker compose -f docker-compose.prod.yml --env-file .env.production up -d

# Verify all containers are healthy
docker compose -f docker-compose.prod.yml ps

# Check logs for errors
docker compose -f docker-compose.prod.yml logs
```

### Update Deployment

```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build

# Or rebuild specific service
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build backend
```

### Stop Services

```bash
# Stop all services (keeps data)
docker compose -f docker-compose.prod.yml down

# Stop and remove volumes (DESTROYS DATA)
docker compose -f docker-compose.prod.yml down -v
```

### Restart Services

```bash
# Restart all
docker compose -f docker-compose.prod.yml restart

# Restart specific service
docker compose -f docker-compose.prod.yml restart backend
```

---

## SSL Certificate Management

### Automatic Certificates

Traefik automatically:
1. Obtains certificates from Let's Encrypt
2. Renews certificates before expiry
3. Stores certificates in `traefik_letsencrypt` volume

### Staging Mode (Testing)

To avoid Let's Encrypt rate limits during testing, use staging:

```bash
# In docker-compose.prod.yml, uncomment:
# - "--certificatesresolvers.letsencrypt.acme.caserver=https://acme-staging-v02.api.letsencrypt.org/directory"
```

### Certificate Troubleshooting

```bash
# Check certificate status
docker exec domos-traefik cat /letsencrypt/acme.json | jq '.letsencrypt.Certificates'

# Force certificate renewal
docker compose -f docker-compose.prod.yml restart traefik
```

---

## Database Management

### Backup

```bash
# Create backup
docker exec domos-db-prod pg_dump -U postgres domos_cashier > backup_$(date +%Y%m%d_%H%M%S).sql

# Automated daily backup (add to crontab)
0 2 * * * docker exec domos-db-prod pg_dump -U postgres domos_cashier > /backups/domos_$(date +\%Y\%m\%d).sql
```

### Restore

```bash
# Restore from backup
cat backup_20260625.sql | docker exec -i domos-db-prod psql -U postgres domos_cashier
```

### Database Access

```bash
# Interactive psql
docker exec -it domos-db-prod psql -U postgres domos_cashier

# Run SQL command
docker exec domos-db-prod psql -U postgres domos_cashier -c "SELECT COUNT(*) FROM apartments;"
```

---

## Health Checks

### Endpoints

| Service | Endpoint | Expected Response |
|---------|----------|-------------------|
| Backend | `https://yourdomain.com/health` | `{"status": "healthy"}` |
| Frontend | `https://yourdomain.com/` | HTML page |
| Traefik Dashboard | `https://traefik.yourdomain.com/` | Dashboard UI |

### Manual Health Check

```bash
# Check backend health
curl -s https://yourdomain.com/health | jq

# Check all container health
docker compose -f docker-compose.prod.yml ps
```

---

## Security Checklist

### Before Going Live

- [ ] Change default Traefik dashboard password
- [ ] Generate strong `SECRET_KEY` (min 32 chars)
- [ ] Generate strong `POSTGRES_PASSWORD`
- [ ] Verify HTTPS is working
- [ ] Test rate limiting is active
- [ ] Disable API docs in production (optional)
- [ ] Set up firewall (only ports 80, 443)
- [ ] Configure backup automation
- [ ] Set up monitoring/alerting

### Security Headers Applied

Traefik automatically adds these security headers:
- `Strict-Transport-Security` (HSTS) - 1 year
- `X-Content-Type-Options: nosniff`
- `X-XSS-Protection: 1; mode=block`
- `X-Frame-Options: DENY`
- `X-Robots-Tag: noindex,nofollow`

---

## Troubleshooting

### Common Issues

**Certificate not issued:**
```bash
# Check Traefik logs for ACME errors
docker compose -f docker-compose.prod.yml logs traefik | grep -i acme

# Verify DNS is pointing to server
dig +short yourdomain.com
```

**Backend unhealthy:**
```bash
# Check backend logs
docker compose -f docker-compose.prod.yml logs backend

# Check database connection
docker exec domos-backend-prod python -c "from app.db.session import engine; print(engine.url)"
```

**Rate limit too aggressive:**
```bash
# Increase limits temporarily via environment
export RATE_LIMIT_API_AVG=500
docker compose -f docker-compose.prod.yml --env-file .env.production up -d
```

**502 Bad Gateway:**
```bash
# Check if backend is running
docker compose -f docker-compose.prod.yml ps backend

# Check backend logs for errors
docker compose -f docker-compose.prod.yml logs --tail=50 backend
```

**503 Service Unavailable:**
```bash
# Check if services are healthy
docker compose -f docker-compose.prod.yml ps

# Restart unhealthy service
docker compose -f docker-compose.prod.yml restart backend
```

---

## Architecture Diagram

```
                              Internet
                                  │
                          ┌───────▼───────┐
                          │  Ports 80/443 │
                          └───────┬───────┘
                                  │
┌─────────────────────────────────▼─────────────────────────────────┐
│                         Traefik Proxy                              │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ • Automatic HTTPS (Let's Encrypt)                           │  │
│  │ • Rate Limiting (100/min API, 5/min Auth)                   │  │
│  │ • Security Headers (HSTS, XSS, etc.)                        │  │
│  │ • Request Routing                                           │  │
│  │ • JSON Access Logging                                       │  │
│  └─────────────────────────────────────────────────────────────┘  │
└──────────┬────────────────────┬────────────────────┬──────────────┘
           │                    │                    │
    ┌──────▼──────┐      ┌──────▼──────┐      ┌──────▼──────┐
    │  /api/auth  │      │   /api/*    │      │     /*      │
    │  (5/min)    │      │  (100/min)  │      │  (frontend) │
    └──────┬──────┘      └──────┬──────┘      └──────┬──────┘
           │                    │                    │
           └────────────┬───────┘                    │
                        │                            │
                ┌───────▼───────┐            ┌───────▼───────┐
                │    Backend    │            │   Frontend    │
                │   (FastAPI)   │            │    (Nginx)    │
                │   Port 8000   │            │    Port 80    │
                └───────┬───────┘            └───────────────┘
                        │
                ┌───────▼───────┐
                │  PostgreSQL   │
                │   Port 5432   │
                └───────────────┘
```

---

## Monitoring Scripts

### Rate Limit Monitor

Create `scripts/monitor-ratelimits.sh`:

```bash
#!/bin/bash
# Monitor rate limit events in real-time

echo "Monitoring rate limit events (HTTP 429)..."
echo "Press Ctrl+C to stop"
echo ""

docker exec domos-traefik tail -f /var/log/traefik/access.log 2>/dev/null | \
  jq -r 'select(.DownstreamStatus == 429) | 
    "\(.StartUTC | split(".")[0])Z | \(.ClientHost) | \(.RequestMethod) \(.RequestPath) | 429 Too Many Requests"'
```

### Daily Rate Limit Report

Create `scripts/ratelimit-report.sh`:

```bash
#!/bin/bash
# Generate daily rate limit report

TODAY=$(date -u +%Y-%m-%d)
LOG_FILE="/tmp/traefik_access.log"

# Copy log from container
docker exec domos-traefik cat /var/log/traefik/access.log > $LOG_FILE 2>/dev/null

if [ ! -s $LOG_FILE ]; then
    echo "No log data available"
    exit 1
fi

echo "=== Rate Limit Report for $TODAY ==="
echo ""

echo "Total 429 responses today:"
cat $LOG_FILE | jq -r "select(.DownstreamStatus == 429 and (.StartUTC | startswith(\"$TODAY\")))" | wc -l
echo ""

echo "Top 10 IPs hitting rate limits:"
cat $LOG_FILE | jq -r "select(.DownstreamStatus == 429 and (.StartUTC | startswith(\"$TODAY\"))) | .ClientHost" | \
  sort | uniq -c | sort -rn | head -10
echo ""

echo "Rate limited endpoints:"
cat $LOG_FILE | jq -r "select(.DownstreamStatus == 429 and (.StartUTC | startswith(\"$TODAY\"))) | .RequestPath" | \
  sort | uniq -c | sort -rn
echo ""

echo "Hourly distribution:"
cat $LOG_FILE | jq -r "select(.DownstreamStatus == 429 and (.StartUTC | startswith(\"$TODAY\"))) | .StartUTC[:13]" | \
  sort | uniq -c

rm -f $LOG_FILE
```

---

## Maintenance

### Log Rotation

Traefik logs are stored in a Docker volume. For log rotation, add to crontab:

```bash
# Rotate Traefik access logs weekly
0 0 * * 0 docker exec domos-traefik sh -c 'mv /var/log/traefik/access.log /var/log/traefik/access.log.old && touch /var/log/traefik/access.log'
```

### Volume Cleanup

```bash
# Remove unused volumes (careful!)
docker volume prune

# Check volume sizes
docker system df -v
```

### Update Traefik

```bash
# Pull latest Traefik image
docker compose -f docker-compose.prod.yml pull traefik

# Restart with new image
docker compose -f docker-compose.prod.yml up -d traefik
```

---

## Quick Reference

### Environment Variables Summary

| Variable | Default | Description |
|----------|---------|-------------|
| `DOMAIN` | localhost | Your domain name |
| `ACME_EMAIL` | admin@example.com | Let's Encrypt email |
| `SECRET_KEY` | (required) | JWT signing key |
| `POSTGRES_PASSWORD` | (required) | Database password |
| `RATE_LIMIT_API_AVG` | 100 | API requests/period |
| `RATE_LIMIT_API_BURST` | 50 | API burst allowance |
| `RATE_LIMIT_AUTH_AVG` | 5 | Auth requests/period |
| `RATE_LIMIT_AUTH_BURST` | 10 | Auth burst allowance |
| `RATE_LIMIT_IP_DEPTH` | 1 | Proxy depth for IP |
| `TRAEFIK_LOG_LEVEL` | INFO | Log verbosity |

### Common Commands

```bash
# Deploy
docker compose -f docker-compose.prod.yml --env-file .env.production up -d

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Restart
docker compose -f docker-compose.prod.yml restart

# Stop
docker compose -f docker-compose.prod.yml down

# Backup database
docker exec domos-db-prod pg_dump -U postgres domos_cashier > backup.sql

# Check rate limits
docker exec domos-traefik cat /var/log/traefik/access.log | jq 'select(.DownstreamStatus == 429)'
```

---

*Last updated: 2026-06-25*