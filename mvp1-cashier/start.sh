#!/bin/bash

# =============================================================================
# DomOS Cashier MVP - Автоматичен скрипт за стартиране
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$SCRIPT_DIR/backend"
FRONTEND_DIR="$SCRIPT_DIR/frontend"
DB_NAME="domos_cashier"
BACKEND_PORT=8000
FRONTEND_PORT=5173

print_header() { echo -e "${BLUE}\n╔═══════════════════════════════════════════════════════════════╗\n║           🏠 DomOS Cashier MVP - Стартиране                   ║\n╚═══════════════════════════════════════════════════════════════╝${NC}\n"; }
print_step() { echo -e "${YELLOW}▶ $1${NC}"; }
print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_info() { echo -e "${BLUE}ℹ $1${NC}"; }
check_command() { command -v "$1" &>/dev/null; }

install_system_dependencies() {
    print_step "Проверка и инсталиране на системни зависимости..."
    local packages=""
    check_command psql || packages="$packages postgresql postgresql-client"
    [ ! -f "/usr/include/python3.13/Python.h" ] && [ ! -f "/usr/include/python3.12/Python.h" ] && packages="$packages python3-dev"
    [ ! -f "/usr/include/postgresql/libpq-fe.h" ] && packages="$packages libpq-dev"
    check_command gcc || packages="$packages build-essential"
    if [ -n "$packages" ]; then
        print_info "Инсталиране на:$packages"
        apt-get update -qq 2>/dev/null
        DEBIAN_FRONTEND=noninteractive apt-get install -y -qq $packages >/dev/null 2>&1
        print_success "Системни зависимости инсталирани"
    else
        print_success "Всички системни зависимости са налични"
    fi
    echo ""
}

start_postgresql_service() {
    print_step "Проверка на PostgreSQL сървис..."
    if ! pg_isready -q 2>/dev/null; then
        print_info "Стартиране на PostgreSQL сървис..."
        service postgresql start >/dev/null 2>&1 || true
        local retries=10
        while [ $retries -gt 0 ]; do
            pg_isready -q 2>/dev/null && break
            sleep 1
            retries=$((retries - 1))
        done
        pg_isready -q 2>/dev/null && print_success "PostgreSQL сървис стартиран" || { print_error "PostgreSQL не успя да стартира"; exit 1; }
    else
        print_success "PostgreSQL сървис работи"
    fi
    echo ""
}

check_prerequisites() {
    print_step "Проверка на предварителни изисквания..."
    local missing=0
    check_command python3 && print_success "Python: $(python3 --version 2>&1 | cut -d' ' -f2)" || { print_error "python3 не е инсталиран!"; missing=1; }
    check_command node && print_success "Node.js: $(node --version)" || { print_error "node не е инсталиран!"; missing=1; }
    check_command npm && print_success "npm: $(npm --version)" || { print_error "npm не е инсталиран!"; missing=1; }
    check_command psql && print_success "PostgreSQL: $(psql --version | head -1)" || { print_error "PostgreSQL не е наличен"; missing=1; }
    [ $missing -eq 1 ] && { print_error "Липсващи компоненти."; exit 1; }
    echo ""
}

setup_database() {
    print_step "Проверка на база данни..."
    if sudo -u postgres psql -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
        print_success "База данни '$DB_NAME' съществува"
    else
        print_info "Създаване на база данни '$DB_NAME'..."
        sudo -u postgres createdb "$DB_NAME" 2>/dev/null || createdb "$DB_NAME" 2>/dev/null || { print_error "Не може да се създаде база данни."; exit 1; }
        print_success "База данни '$DB_NAME' създадена"
    fi
    echo ""
}

setup_backend() {
    print_step "Настройка на Backend..."
    cd "$BACKEND_DIR"
    [ ! -d "venv" ] && { print_info "Създаване на виртуална среда..."; python3 -m venv venv; print_success "Виртуална среда създадена"; } || print_success "Виртуална среда съществува"
    source venv/bin/activate
    print_info "Инсталиране на Python зависимости..."
    pip install -q --upgrade pip 2>/dev/null
    pip install -q -r requirements.txt 2>/dev/null
    print_success "Python зависимости инсталирани"
    [ ! -f ".env" ] && { print_info "Създаване на .env файл..."; cat > .env << EOF
DATABASE_URL=postgresql://postgres:postgres@localhost/$DB_NAME
SECRET_KEY=your-secret-key-$(date +%s)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
EOF
    print_success ".env файл създаден"; }
    print_info "Инициализация на базата данни..."
    python init_db.py 2>/dev/null || print_info "Базата вече е инициализирана"
    print_success "База данни инициализирана"
    deactivate
    echo ""
}

setup_frontend() {
    print_step "Настройка на Frontend..."
    cd "$FRONTEND_DIR"
    [ ! -d "node_modules" ] && { print_info "Инсталиране на npm зависимости..."; npm install --silent 2>/dev/null; print_success "npm зависимости инсталирани"; } || print_success "npm зависимости вече са инсталирани"
    echo ""
}

start_backend() {
    print_step "Стартиране на Backend (порт $BACKEND_PORT)..."
    cd "$BACKEND_DIR"
    source venv/bin/activate
    lsof -Pi :$BACKEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1 && { print_info "Порт $BACKEND_PORT е зает. Спиране..."; kill $(lsof -Pi :$BACKEND_PORT -sTCP:LISTEN -t) 2>/dev/null || true; sleep 2; }
    nohup uvicorn app.main:app --host 0.0.0.0 --port $BACKEND_PORT > /tmp/domos_backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > /tmp/domos_backend.pid
    sleep 3
    kill -0 $BACKEND_PID 2>/dev/null && print_success "Backend стартиран (PID: $BACKEND_PID)" || { print_error "Backend не успя да стартира."; tail -20 /tmp/domos_backend.log; exit 1; }
    deactivate
}

start_frontend() {
    print_step "Стартиране на Frontend (порт $FRONTEND_PORT)..."
    cd "$FRONTEND_DIR"
    lsof -Pi :$FRONTEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1 && { print_info "Порт $FRONTEND_PORT е зает. Спиране..."; kill $(lsof -Pi :$FRONTEND_PORT -sTCP:LISTEN -t) 2>/dev/null || true; sleep 2; }
    nohup npm run dev -- --host > /tmp/domos_frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > /tmp/domos_frontend.pid
    sleep 5
    kill -0 $FRONTEND_PID 2>/dev/null && print_success "Frontend стартиран (PID: $FRONTEND_PID)" || { print_error "Frontend не успя да стартира."; tail -20 /tmp/domos_frontend.log; exit 1; }
}

show_info() {
    echo ""
    echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║           🎉 DomOS Cashier MVP стартиран успешно!             ║${NC}"
    echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
    echo -e "\n${BLUE}📊 Достъп:${NC}"
    echo "   Frontend:     http://localhost:$FRONTEND_PORT"
    echo "   Backend API:  http://localhost:$BACKEND_PORT"
    echo "   Swagger UI:   http://localhost:$BACKEND_PORT/docs"
    echo -e "\n${BLUE}🔐 Тестови потребители:${NC}"
    echo "   Админ:   admin / admin123"
    echo "   Касиер:  cecka / 1234"
    echo -e "\n${BLUE}📝 Логове:${NC}"
    echo "   Backend:  /tmp/domos_backend.log"
    echo "   Frontend: /tmp/domos_frontend.log"
    echo -e "\n${YELLOW}За спиране: $SCRIPT_DIR/stop.sh${NC}\n"
}

# Main
print_header
install_system_dependencies
start_postgresql_service
check_prerequisites
setup_database
setup_backend
setup_frontend
start_backend
start_frontend
show_info
