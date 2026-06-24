#!/bin/bash
# DomOS Cashier MVP - Production Entrypoint Script
# Strict validation, no demo data, health checks before starting

set -e

echo "🏭 Starting DomOS Cashier Backend (PRODUCTION MODE)..."

# Function to validate required environment variables
validate_env() {
    echo "🔍 Validating required environment variables..."
    
    local required_vars=(
        "DATABASE_URL"
        "SECRET_KEY"
        "ENVIRONMENT"
    )
    
    local missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        echo "❌ CRITICAL ERROR: Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            echo "   - $var"
        done
        echo ""
        echo "Please set all required variables in your .env.production file"
        exit 1
    fi
    
    # Validate ENVIRONMENT is set to production
    if [ "$ENVIRONMENT" != "production" ]; then
        echo "⚠️  WARNING: ENVIRONMENT is set to '$ENVIRONMENT' but running production entrypoint"
        echo "   Consider using entrypoint.sh for non-production environments"
    fi
    
    # Warn if SECRET_KEY looks like a default/weak value
    if [ ${#SECRET_KEY} -lt 32 ]; then
        echo "⚠️  WARNING: SECRET_KEY is shorter than 32 characters - not recommended for production"
    fi
    
    echo "✅ All required environment variables are set"
}

# Function to check for dangerous flags in production
check_production_safety() {
    echo "🛡️  Checking production safety flags..."
    
    # INIT_DB must NEVER be true in production
    if [ "$INIT_DB" = "true" ]; then
        echo "❌ CRITICAL ERROR: INIT_DB=true is not allowed in production!"
        echo "   Demo/seed data should never be initialized in production environment"
        echo "   Remove INIT_DB from your .env.production file"
        exit 1
    fi
    
    # Warn about DEBUG mode
    if [ "$DEBUG" = "true" ] || [ "$DEBUG" = "1" ]; then
        echo "⚠️  WARNING: DEBUG mode is enabled in production - this is not recommended"
    fi
    
    echo "✅ Production safety checks passed"
}

# Function to wait for database
wait_for_db() {
    echo "⏳ Waiting for database to be ready..."
    
    # Extract host and port from DATABASE_URL
    # DATABASE_URL format: postgresql://user:pass@host:port/dbname
    DB_HOST=$(echo $DATABASE_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
    DB_PORT=$(echo $DATABASE_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
    
    # Default values if extraction fails
    DB_HOST=${DB_HOST:-db}
    DB_PORT=${DB_PORT:-5432}
    
    max_attempts=30
    attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if python -c "import socket; s = socket.socket(); s.settimeout(1); s.connect(('$DB_HOST', $DB_PORT)); s.close()" 2>/dev/null; then
            echo "✅ Database is ready!"
            return 0
        fi
        echo "   Attempt $attempt/$max_attempts - Database not ready yet..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "❌ Database connection failed after $max_attempts attempts"
    exit 1
}

# Function to check if database is empty
is_database_empty() {
    echo "🔍 Checking database state..."
    
    # Check if alembic_version table exists and has data
    result=$(python -c "
import os
import sys
from sqlalchemy import create_engine, text

try:
    engine = create_engine(os.environ['DATABASE_URL'])
    with engine.connect() as conn:
        # Check if alembic_version table exists
        result = conn.execute(text(
            \"SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='alembic_version')\"
        )).scalar()
        
        if not result:
            print('EMPTY')
            sys.exit(0)
        
        # Check if there are any migrations applied
        result = conn.execute(text('SELECT COUNT(*) FROM alembic_version')).scalar()
        if result == 0:
            print('EMPTY')
        else:
            print('NOT_EMPTY')
except Exception as e:
    print('ERROR')
    sys.exit(1)
" 2>/dev/null)
    
    if [ "$result" = "ERROR" ]; then
        echo "❌ Failed to check database state"
        exit 1
    fi
    
    if [ "$result" = "EMPTY" ]; then
        echo "📭 Database is empty - first production deployment detected"
        return 0
    else
        echo "📦 Database already initialized"
        return 1
    fi
}

# Function to run migrations
run_migrations() {
    echo "📦 Running database migrations..."
    
    # Check if alembic directory exists
    if [ -d "alembic" ]; then
        # Run alembic migrations
        alembic upgrade head
        echo "✅ Migrations completed!"
    else
        echo "❌ ERROR: No alembic directory found"
        exit 1
    fi
}

# Function to initialize production users (first deployment only)
init_production_users() {
    echo "👥 Initializing production users (first deployment)..."
    
    # Check if init_users.py exists
    if [ -f "init_users.py" ]; then
        python init_users.py
        echo "✅ Production users initialized!"
        echo "⚠️  IMPORTANT: Change default passwords immediately after first login!"
    else
        echo "⚠️  WARNING: No init_users.py found"
        echo "   You will need to manually create admin users"
    fi
}

# Function to perform application health check
health_check() {
    echo "🏥 Performing application health check..."
    
    # Basic Python import test
    python -c "
import sys
try:
    from app.main import app
    from app.db.session import get_db
    print('OK')
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
" 2>&1
    
    if [ $? -ne 0 ]; then
        echo "❌ Application health check failed - cannot import core modules"
        exit 1
    fi
    
    echo "✅ Application health check passed"
}

# Main execution flow for production
echo "🔒 Running in PRODUCTION mode with strict validation"
echo "====================================================="

# Step 1: Validate environment
validate_env

# Step 2: Check production safety
check_production_safety

# Step 3: Wait for database
wait_for_db

# Step 4: Database initialization logic
if is_database_empty; then
    echo ""
    echo "🆕 First production deployment detected"
    echo "Running initial setup: migrations + user initialization"
    echo ""
    
    run_migrations
    init_production_users
    
    echo ""
    echo "✅ Initial production setup completed successfully"
    echo "⚠️  NEXT STEPS:"
    echo "   1. Login with default admin credentials"
    echo "   2. IMMEDIATELY change all default passwords"
    echo "   3. Create additional users as needed"
    echo "   4. Configure production-specific settings"
    echo ""
else
    # Database exists - only run migrations (safe idempotent operation)
    echo ""
    echo "📊 Existing database detected - running migrations only"
    echo ""
    
    run_migrations
fi

# Step 5: Health check before starting server
health_check

# Step 6: Start production server
echo ""
echo "====================================================="
echo "🚀 Starting production uvicorn server..."
echo "   Environment: $ENVIRONMENT"
echo "   Database: Connected"
echo "   Migrations: Up to date"
echo "====================================================="
echo ""

# Production server configuration:
# - No auto-reload (use --reload in development only)
# - Proper worker configuration should be handled by process manager (systemd, supervisor, etc.)
# - Use --proxy-headers for reverse proxy setups
# - Log level can be controlled via LOG_LEVEL env var

exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --proxy-headers \
    --forwarded-allow-ips='*' \
    --log-level ${LOG_LEVEL:-info} \
    "$@"
