#!/bin/bash
# Проверка работы Time Tracker сервиса
# Использование: ./check_service.sh

SERVICE_NAME="time-tracker"
HEALTH_URL="http://localhost:8001/health"
LOG_FILE="/var/log/time-tracker/check_$(date +%Y%m%d_%H%M%S).log"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция логирования
log() {
    echo -e "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Функция проверки статуса сервиса
check_service_status() {
    if systemctl is-active --quiet "$SERVICE_NAME" 2>/dev/null; then
        echo -e "${GREEN}✅ Сервис $SERVICE_NAME активен${NC}"
        return 0
    else
        echo -e "${RED}❌ Сервис $SERVICE_NAME не активен${NC}"
        return 1
    fi
}

# Функция проверки health endpoint
check_health() {
    if curl -s --max-time 10 --head "$HEALTH_URL" >/dev/null 2>&1; then
        echo -e "${GREEN}✅ Health check пройден${NC}"
        return 0
    else
        echo -e "${RED}❌ Health check не пройден${NC}"
        return 1
    fi
}

# Функция проверки порта
check_port() {
    if netstat -tlnp 2>/dev/null | grep -q ":8001 "; then
        echo -e "${GREEN}✅ Порт 8001 слушается${NC}"
        return 0
    else
        echo -e "${RED}❌ Порт 8001 не слушается${NC}"
        return 1
    fi
}

# Функция проверки процессов
check_processes() {
    PYTHON_PROCESSES=$(pgrep -f "python.*cloud_deploy.py" | wc -l)
    if [ "$PYTHON_PROCESSES" -gt 0 ]; then
        echo -e "${GREEN}✅ Найдено $PYTHON_PROCESSES Python процесса(ов)${NC}"
        return 0
    else
        echo -e "${RED}❌ Python процессы не найдены${NC}"
        return 1
    fi
}

# Функция проверки использования ресурсов
check_resources() {
    echo -e "${BLUE}📊 Использование ресурсов:${NC}"

    # CPU
    CPU_USAGE=$(top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1}')
    echo -e "   CPU: ${YELLOW}$(printf "%.1f" $CPU_USAGE)%${NC}"

    # Память
    MEM_INFO=$(free | grep Mem)
    MEM_TOTAL=$(echo $MEM_INFO | awk '{print $2}')
    MEM_USED=$(echo $MEM_INFO | awk '{print $3}')
    MEM_PERCENT=$((MEM_USED * 100 / MEM_TOTAL))
    echo -e "   Память: ${YELLOW}$MEM_PERCENT%${NC} ($((MEM_USED/1024))MB из $((MEM_TOTAL/1024))MB)"

    # Диск
    DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
    echo -e "   Диск: ${YELLOW}$DISK_USAGE%${NC}"
}

# Функция показа статуса systemd
show_systemd_status() {
    echo -e "${BLUE}🔧 Статус systemd сервиса:${NC}"
    systemctl status "$SERVICE_NAME" --no-pager -l 2>/dev/null || echo "Сервис не найден"
}

# Функция показа последних логов
show_recent_logs() {
    echo -e "${BLUE}📝 Последние логи сервиса:${NC}"
    journalctl -u "$SERVICE_NAME" -n 10 --no-pager 2>/dev/null || echo "Логи не найдены"
}

# Основная функция
main() {
    echo -e "${BLUE}🔍 Проверка работы Time Tracker$(date '+%Y-%m-%d %H:%M:%S')${NC}"
    echo "=================================================="

    # Создание директории для логов
    mkdir -p /var/log/time-tracker 2>/dev/null

    # Выполнение проверок
    local all_checks_passed=true

    log "Начало проверки сервиса"

    if ! check_service_status; then
        all_checks_passed=false
    fi

    if ! check_port; then
        all_checks_passed=false
    fi

    if ! check_health; then
        all_checks_passed=false
    fi

    if ! check_processes; then
        all_checks_passed=false
    fi

    echo
    check_resources
    echo

    if [ "$1" = "--full" ]; then
        show_systemd_status
        echo
        show_recent_logs
        echo
    fi

    # Итоговый статус
    echo "=================================================="
    if $all_checks_passed; then
        log "✅ Все проверки пройдены успешно"
        echo -e "${GREEN}🎉 Все проверки пройдены успешно!${NC}"
        exit 0
    else
        log "❌ Некоторые проверки не пройдены"
        echo -e "${RED}⚠️  Некоторые проверки не пройдены${NC}"
        echo -e "${YELLOW}💡 Рекомендации:${NC}"
        echo "   - Проверьте логи: journalctl -u $SERVICE_NAME -f"
        echo "   - Перезапустите сервис: sudo systemctl restart $SERVICE_NAME"
        echo "   - Проверьте конфигурацию: sudo systemctl status $SERVICE_NAME"
        exit 1
    fi
}

# Обработка аргументов
case "$1" in
    --help|-h)
        echo "Использование: $0 [опции]"
        echo ""
        echo "Опции:"
        echo "  --full     Полная проверка с логами и статусом systemd"
        echo "  --help     Показать эту справку"
        echo ""
        echo "Примеры:"
        echo "  $0              Быстрая проверка"
        echo "  $0 --full       Полная проверка"
        exit 0
        ;;
    *)
        main "$1"
        ;;
esac