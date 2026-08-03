#!/bin/bash

# =============================================================================
# DomOS MVP1 Cashier - Development Environment Stop Script
# For use inside Agent Zero Docker container
# =============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Stop frontend
stop_frontend() {
    log_info "Stopping frontend..."
    
    if [ -f /tmp/frontend.pid ]; then
        local pid=$(cat /tmp/frontend.pid)
        if kill -0 $pid 2>/dev/null; then
            kill $pid 2>/dev/null
            rm -f /tmp/frontend.pid
            log_success "Frontend stopped (PID: $pid)"
        else
            rm -f /tmp/frontend.pid
            log_warning "Frontend was not running"
        fi
    else
        # Try to find and kill by port
        local pids=$(lsof -ti:5173 2>/dev/null)
        if [ -n "$pids" ]; then
            echo "$pids" | xargs kill 2>/dev/null
            log_success "Frontend stopped (found by port 5173)"
        else
            log_warning "Frontend was not running"
        fi
    fi
}

# Stop backend
stop_backend() {
    log_info "Stopping backend..."
    
    if [ -f /tmp/backend.pid ]; then
        local pid=$(cat /tmp/backend.pid)
        if kill -0 $pid 2>/dev/null; then
            kill $pid 2>/dev/null
            rm -f /tmp/backend.pid
            log_success "Backend stopped (PID: $pid)"
        else
            rm -f /tmp/backend.pid
            log_warning "Backend was not running"
        fi
    else
        # Try to find and kill by port
        local pids=$(lsof -ti:8000 2>/dev/null)
        if [ -n "$pids" ]; then
            echo "$pids" | xargs kill 2>/dev/null
            log_success "Backend stopped (found by port 8000)"
        else
            log_warning "Backend was not running"
        fi
    fi
}

# Stop PostgreSQL (optional)
stop_postgresql() {
    if [ "$1" = "--all" ]; then
        log_info "Stopping PostgreSQL..."
        su - postgres -c "/usr/lib/postgresql/*/bin/pg_ctl -D /var/lib/postgresql/data stop" 2>/dev/null || \
        service postgresql stop 2>/dev/null || true
        log_success "PostgreSQL stop requested"
    fi
}

# Main
main() {
    echo ""
    echo "========================================"
    echo "  DomOS MVP1 Cashier - Stopping Dev    "
    echo "========================================"
    echo ""
    
    stop_frontend
    stop_backend
    stop_postgresql "$1"
    
    echo ""
    log_success "Development services stopped"
    
    if [ "$1" != "--all" ]; then
        log_info "Note: PostgreSQL is still running. Use --all flag to stop it too."
    fi
    echo ""
}

main "$@"
