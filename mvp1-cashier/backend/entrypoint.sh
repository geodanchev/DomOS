#!/bin/bash
# DomOS Cashier MVP - Backend Entrypoint Script
# Automatically detects empty database and runs migrations + initialization

set -e

echo "🚀 Starting DomOS Cashier Backend..."

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
    echo "🔍 Checking if database is empty..."
    
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
    # If any error occurs, assume database is empty (safe default)
    print('EMPTY')
" 2>/dev/null)
    
    if [ "$result" = "EMPTY" ]; then
        echo "📭 Database is empty - first run detected"
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
        echo "⚠️  No alembic directory found, skipping migrations"
    fi
}

# Function to initialize database with users
init_users() {
    echo "👥 Initializing users..."
    
    # Check if init_users.py exists
    if [ -f "init_users.py" ]; then
        python init_users.py
        echo "✅ Users initialized!"
    else
        echo "⚠️  No init_users.py found, skipping user initialization"
    fi
}

# Function to initialize database with seed data (optional)
init_database() {
    echo "🌱 Initializing database with seed data..."
    
    # Check if init_db.py exists
    if [ -f "init_db.py" ]; then
        python init_db.py
        echo "✅ Database seed data initialized!"
    else
        echo "⚠️  No init_db.py found, skipping seed data initialization"
    fi
}

# Main execution flow
wait_for_db

# Automatic detection: if database is empty, run migrations and init
if is_database_empty; then
    echo "🆕 First run detected - running full initialization..."
    run_migrations
    init_users
    
    # Only run seed data if explicitly requested via INIT_DB flag
    # This allows first-run user init without forcing demo data
    if [ "$INIT_DB" = "true" ]; then
        init_database
    fi
else
    # Database exists - only run migrations (safe to run multiple times)
    run_migrations
    
    # Optionally allow manual re-initialization if INIT_DB is explicitly set
    if [ "$INIT_DB" = "true" ]; then
        echo "⚠️  INIT_DB flag set - running initialization on existing database"
        init_database
    fi
fi

echo "🎉 Starting uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 "$@"
