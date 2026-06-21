#!/bin/bash
# DomOS Cashier MVP - Backend Entrypoint Script
# This script waits for the database and runs migrations before starting the app

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

# Function to initialize database with seed data
init_database() {
    echo "🌱 Initializing database..."
    
    # Check if init_db.py exists
    if [ -f "init_db.py" ]; then
        python init_db.py
        echo "✅ Database initialized!"
    else
        echo "⚠️  No init_db.py found, skipping initialization"
    fi
}

# Main execution
wait_for_db
run_migrations

# Only run init if INIT_DB is set to true
if [ "$INIT_DB" = "true" ]; then
    init_database
fi

echo "🎉 Starting uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 "$@"
