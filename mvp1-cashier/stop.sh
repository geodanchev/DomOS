#!/bin/bash

# =============================================================================
# DomOS Cashier MVP - Скрипт за спиране
# =============================================================================

# Цветове за изход
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║           🏠 DomOS Cashier MVP - Спиране                      ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Спиране на Backend
stop_backend() {
    echo -e "${YELLOW}▶ Спиране на Backend...${NC}"
    
    if [ -f /tmp/domos_backend.pid ]; then
        PID=$(cat /tmp/domos_backend.pid)
        if kill -0 $PID 2>/dev/null; then
            kill $PID 2>/dev/null
            sleep 2
            # Force kill ако все още работи
            if kill -0 $PID 2>/dev/null; then
                kill -9 $PID 2>/dev/null
            fi
            print_success "Backend спрян (PID: $PID)"
        else
            print_info "Backend процесът не работи"
        fi
        rm -f /tmp/domos_backend.pid
    else
        # Опит за спиране по порт
        if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
            kill $(lsof -Pi :8000 -sTCP:LISTEN -t) 2>/dev/null
            print_success "Backend спрян (по порт 8000)"
        else
            print_info "Backend не работи"
        fi
    fi
}

# Спиране на Frontend
stop_frontend() {
    echo -e "${YELLOW}▶ Спиране на Frontend...${NC}"
    
    if [ -f /tmp/domos_frontend.pid ]; then
        PID=$(cat /tmp/domos_frontend.pid)
        if kill -0 $PID 2>/dev/null; then
            kill $PID 2>/dev/null
            sleep 2
            # Force kill ако все още работи
            if kill -0 $PID 2>/dev/null; then
                kill -9 $PID 2>/dev/null
            fi
            print_success "Frontend спрян (PID: $PID)"
        else
            print_info "Frontend процесът не работи"
        fi
        rm -f /tmp/domos_frontend.pid
    else
        # Опит за спиране по порт
        if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null 2>&1; then
            kill $(lsof -Pi :5173 -sTCP:LISTEN -t) 2>/dev/null
            print_success "Frontend спрян (по порт 5173)"
        else
            print_info "Frontend не работи"
        fi
    fi
}

# Почистване на логове (опционално)
clean_logs() {
    if [ "$1" == "--clean" ]; then
        echo -e "${YELLOW}▶ Почистване на логове...${NC}"
        rm -f /tmp/domos_backend.log /tmp/domos_frontend.log
        print_success "Логовете са изтрити"
    fi
}

# =============================================================================
# Главна логика
# =============================================================================

print_header
stop_backend
stop_frontend
clean_logs $1

echo ""
print_success "DomOS Cashier MVP е спрян."
echo ""
