#!/bin/bash

# =============================================================================
# DomOS MVP1 Cashier - Development Environment Startup Script
# For use inside Agent Zero Docker container
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="/a0/usr/projects/domos/mvp1-cashier"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
PG_DATA="/var/lib/postgresql/data"
DB_NAME="domos_cashier"
DB_USER="postgres"
DB_PASSWORD="postgres"

# Log functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if a service is running
check_port() {
    local port=$1
    netstat -tuln 2>/dev/null | grep -q ":$port " || ss -tuln 2>/dev/null | grep -q ":$port "
}

# =============================================================================
# PostgreSQL Setup
# =============================================================================
start_postgresql() {
    log_info "Checking PostgreSQL status..."
    
    # Check if PostgreSQL is already running
    if check_port 5432; then
        log_success "PostgreSQL is already running on port 5432"
        return 0
    fi
    
    # Initialize PostgreSQL data directory if needed
    if [ ! -d "$PG_DATA" ] || [ -z "$(ls -A $PG_DATA 2>/dev/null)" ]; then
        log_info "Initializing PostgreSQL data directory..."
        mkdir -p "$PG_DATA"
        chown -R postgres:postgres "$PG_DATA"
        chmod 700 "$PG_DATA"
        su - postgres -c "/usr/lib/postgresql/*/bin/initdb -D $PG_DATA"
    fi
    
    # Start PostgreSQL
    log_info "Starting PostgreSQL..."
    su - postgres -c "/usr/lib/postgresql/*/bin/pg_ctl -D $PG_DATA -l /var/log/postgresql/postgresql.log start" || {
        # Alternative: try service command
        service postgresql start 2>/dev/null || true
    }
    
    # Wait for PostgreSQL to be ready
    local max_attempts=30
    local attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if check_port 5432; then
            log_success "PostgreSQL started successfully"
            break
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
    
    if [ $attempt -eq $max_attempts ]; then
        log_error "Failed to start PostgreSQL"
        return 1
    fi
    
    # Create database if it doesn't exist
    log_info "Checking database $DB_NAME..."
    if ! su - postgres -c "psql -lqt" | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
        log_info "Creating database $DB_NAME..."
        su - postgres -c "createdb $DB_NAME"
        log_success "Database $DB_NAME created"
    else
        log_success "Database $DB_NAME already exists"
    fi
    
    # Set password for postgres user
    su - postgres -c "psql -c \"ALTER USER postgres WITH PASSWORD '$DB_PASSWORD';\"" 2>/dev/null || true
    
    return 0
}

# =============================================================================
# Backend Setup
# =============================================================================
start_backend() {
    log_info "Setting up backend..."
    
    cd "$BACKEND_DIR"
    
    # Activate virtual environment or create it
    if [ ! -d "venv" ]; then
        log_info "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    
    # Install dependencies if needed
    if [ ! -f "venv/.deps_installed" ] || [ "requirements.txt" -nt "venv/.deps_installed" ]; then
        log_info "Installing Python dependencies..."
        pip install --upgrade pip -q
        pip install -r requirements.txt -q
        touch venv/.deps_installed
        log_success "Dependencies installed"
    fi
    
    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        log_info "Creating .env file..."
        cat > .env << EOF
DATABASE_URL=postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME
SECRET_KEY=dev-secret-key-change-in-production-min32chars
DEBUG=true
INIT_DEMO_DATA=true
DEMO_ADMIN_PASSWORD=admin123
DEMO_CASHIER_PASSWORD=cashier123
EOF
        log_success ".env file created"
    fi
    
    # Run database migrations
    log_info "Running database migrations..."
    alembic upgrade head
    log_success "Migrations completed"
    
    # Initialize demo data
    log_info "Initializing demo data..."
    python init_db.py || log_warning "Demo data may already exist"
    
    # Check if backend is already running
    if check_port 8000; then
        log_warning "Backend is already running on port 8000"
        return 0
    fi
    
    # Start backend in background
    log_info "Starting backend server..."
    nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/backend.log 2>&1 &
    echo $! > /tmp/backend.pid
    
    # Wait for backend to be ready
    local max_attempts=30
    local attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if check_port 8000; then
            log_success "Backend started on http://localhost:8000"
            log_info "API docs: http://localhost:8000/docs"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
    
    log_error "Backend failed to start. Check /tmp/backend.log for details"
    return 1
}

# =============================================================================
# Frontend Setup
# =============================================================================
start_frontend() {
    log_info "Setting up frontend..."
    
    cd "$FRONTEND_DIR"
    
    # Install npm dependencies if needed
    if [ ! -d "node_modules" ] || [ "package.json" -nt "node_modules/.package-lock.json" ]; then
        log_info "Installing npm dependencies..."
        npm install --silent
        log_success "Dependencies installed"
    fi
    
    # Check if frontend is already running
    if check_port 5173; then
        log_warning "Frontend is already running on port 5173"
        return 0
    fi
    
    # Start frontend in background
    log_info "Starting frontend server..."
    nohup npm run dev -- --host 0.0.0.0 > /tmp/frontend.log 2>&1 &
    echo $! > /tmp/frontend.pid
    
    # Wait for frontend to be ready
    local max_attempts=60
    local attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if check_port 5173; then
            log_success "Frontend started on http://localhost:5173"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
    
    log_error "Frontend failed to start. Check /tmp/frontend.log for details"
    return 1
}

# =============================================================================
# Status Check
# =============================================================================
show_status() {
    echo ""
    echo "========================================"
    echo "         DomOS Development Status      "
    echo "========================================"
    echo ""
    
    if check_port 5432; then
        echo -e "PostgreSQL:  ${GREEN}● Running${NC} (port 5432)"
    else
        echo -e "PostgreSQL:  ${RED}○ Stopped${NC}"
    fi
    
    if check_port 8000; then
        echo -e "Backend:     ${GREEN}● Running${NC} (http://localhost:8000)"
    else
        echo -e "Backend:     ${RED}○ Stopped${NC}"
    fi
    
    if check_port 5173; then
        echo -e "Frontend:    ${GREEN}● Running${NC} (http://localhost:5173)"
    else
        echo -e "Frontend:    ${RED}○ Stopped${NC}"
    fi
    
    echo ""
    echo "Demo Users:"
    echo "  Admin:    username=admin, password=admin123"
    echo "  Cashier:  username=cashier, password=cashier123"
    echo ""
    echo "Logs:"
    echo "  Backend:  /tmp/backend.log"
    echo "  Frontend: /tmp/frontend.log"
    echo ""
}

# =============================================================================
# Main
# =============================================================================
main() {
    echo ""
    echo "========================================"
    echo "  DomOS MVP1 Cashier - Dev Environment "
    echo "========================================"
    echo ""
    
    # Start services
    start_postgresql || exit 1
    start_backend || exit 1
    start_frontend || exit 1
    
    # Show status
    show_status
    
    log_success "Development environment is ready!"
    echo ""
    echo "To stop services, use: ./stop-dev-local.sh"
    echo ""
}

# Run main function
main
