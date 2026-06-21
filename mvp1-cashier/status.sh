#!/bin/bash

# =============================================================================
# DomOS Cashier MVP - Скрипт за проверка на статус
# =============================================================================

# Цветове за изход
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

BACKEND_PORT=8000
FRONTEND_PORT=5173

print_header() {
    echo -e "${BLUE}"
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║           🏠 DomOS Cashier MVP - Статус                       ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

check_backend() {
    echo -e "${YELLOW}▶ Backend статус:${NC}"
    
    # Проверка по PID файл
    if [ -f /tmp/domos_backend.pid ]; then
        PID=$(cat /tmp/domos_backend.pid)
        if kill -0 $PID 2>/dev/null; then
            echo -e "   ${GREEN}✓ Работи (PID: $PID)${NC}"
            echo -e "   ${BLUE}URL: http://localhost:$BACKEND_PORT${NC}"
            echo -e "   ${BLUE}Swagger: http://localhost:$BACKEND_PORT/docs${NC}"
            
            # Проверка дали отговаря
            if curl -s -o /dev/null -w "%{http_code}" http://localhost:$BACKEND_PORT/docs 2>/dev/null | grep -q "200\|302"; then
                echo -e "   ${GREEN}✓ HTTP отговаря${NC}"
            else
                echo -e "   ${YELLOW}⚠ HTTP не отговаря (може да стартира)${NC}"
            fi
            return 0
        fi
    fi
    
    # Проверка по порт
    if lsof -Pi :$BACKEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        PID=$(lsof -Pi :$BACKEND_PORT -sTCP:LISTEN -t)
        echo -e "   ${GREEN}✓ Работи на порт $BACKEND_PORT (PID: $PID)${NC}"
        return 0
    fi
    
    echo -e "   ${RED}✗ Не работи${NC}"
    return 1
}

check_frontend() {
    echo ""
    echo -e "${YELLOW}▶ Frontend статус:${NC}"
    
    # Проверка по PID файл
    if [ -f /tmp/domos_frontend.pid ]; then
        PID=$(cat /tmp/domos_frontend.pid)
        if kill -0 $PID 2>/dev/null; then
            echo -e "   ${GREEN}✓ Работи (PID: $PID)${NC}"
            echo -e "   ${BLUE}URL: http://localhost:$FRONTEND_PORT${NC}"
            
            # Проверка дали отговаря
            if curl -s -o /dev/null -w "%{http_code}" http://localhost:$FRONTEND_PORT 2>/dev/null | grep -q "200\|304"; then
                echo -e "   ${GREEN}✓ HTTP отговаря${NC}"
            else
                echo -e "   ${YELLOW}⚠ HTTP не отговаря (може да стартира)${NC}"
            fi
            return 0
        fi
    fi
    
    # Проверка по порт
    if lsof -Pi :$FRONTEND_PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        PID=$(lsof -Pi :$FRONTEND_PORT -sTCP:LISTEN -t)
        echo -e "   ${GREEN}✓ Работи на порт $FRONTEND_PORT (PID: $PID)${NC}"
        return 0
    fi
    
    echo -e "   ${RED}✗ Не работи${NC}"
    return 1
}

check_database() {
    echo ""
    echo -e "${YELLOW}▶ PostgreSQL статус:${NC}"
    
    if command -v pg_isready &> /dev/null; then
        if pg_isready -q 2>/dev/null; then
            echo -e "   ${GREEN}✓ PostgreSQL работи${NC}"
            
            # Проверка за базата
            if psql -lqt 2>/dev/null | cut -d \| -f 1 | grep -qw "domos_cashier"; then
                echo -e "   ${GREEN}✓ База 'domos_cashier' съществува${NC}"
            else
                echo -e "   ${YELLOW}⚠ База 'domos_cashier' не съществува${NC}"
            fi
            return 0
        fi
    fi
    
    echo -e "   ${RED}✗ PostgreSQL не работи или не е достъпен${NC}"
    return 1
}

show_logs_info() {
    echo ""
    echo -e "${YELLOW}▶ Логове:${NC}"
    
    if [ -f /tmp/domos_backend.log ]; then
        SIZE=$(du -h /tmp/domos_backend.log | cut -f1)
        echo -e "   Backend:  /tmp/domos_backend.log ($SIZE)"
    else
        echo -e "   Backend:  ${BLUE}няма лог файл${NC}"
    fi
    
    if [ -f /tmp/domos_frontend.log ]; then
        SIZE=$(du -h /tmp/domos_frontend.log | cut -f1)
        echo -e "   Frontend: /tmp/domos_frontend.log ($SIZE)"
    else
        echo -e "   Frontend: ${BLUE}няма лог файл${NC}"
    fi
}

show_summary() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    
    local all_running=true
    
    if ! check_backend > /dev/null 2>&1; then
        all_running=false
    fi
    
    if ! check_frontend > /dev/null 2>&1; then
        all_running=false
    fi
    
    if [ "$all_running" = true ]; then
        echo -e "${GREEN}🎉 Всички компоненти работят!${NC}"
    else
        echo -e "${YELLOW}⚠ Някои компоненти не работят. Стартирайте с ./start.sh${NC}"
    fi
    echo ""
}

# =============================================================================
# Главна логика
# =============================================================================

print_header
check_backend
check_frontend
check_database
show_logs_info
show_summary
