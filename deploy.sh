#!/bin/bash

# Скрипт деплоя Time Tracker
set -e

echo "🚀 Начинаем деплой Time Tracker..."

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

# Проверяем, что мы на сервере
if [[ $EUID -eq 0 ]]; then
   error "Не запускайте этот скрипт от root! Используйте sudo для отдельных команд."
fi

# Переменные
APP_DIR="/opt/time-tracker"
SERVICE_NAME="time-tracker"
DOMAIN="work.maxmobiles.ru"

log "Проверяем зависимости..."

# Проверяем Docker
if ! command -v docker &> /dev/null; then
    error "Docker не установлен. Установите Docker и попробуйте снова."
fi

if ! docker compose version &> /dev/null; then
    error "Docker Compose не установлен. Установите Docker Compose и попробуйте снова."
fi

# Создаем директории
log "Создаем директории..."
sudo mkdir -p $APP_DIR/{data,logs,backups,ssl}
sudo chown -R $USER:$USER $APP_DIR

# Копируем файлы (исключая .git)
log "Копируем файлы приложения..."
if [ -d "$APP_DIR" ]; then
    log "Директория $APP_DIR уже существует, очищаем..."
    sudo rm -rf $APP_DIR/*
fi
# Копируем все файлы кроме .git
for item in ./* ./.*; do
    if [ "$item" != "./." ] && [ "$item" != "./.." ] && [ "$item" != "./.git" ]; then
        cp -r "$item" $APP_DIR/ 2>/dev/null || true
    fi
done
cd $APP_DIR

# Создаем .env файл если его нет
if [ ! -f .env ]; then
    log "Создаем .env файл..."
    cp env.example .env
    warning "ВАЖНО: Отредактируйте файл .env и измените SECRET_KEY и другие настройки!"
fi

# Создаем SSL сертификаты (самоподписанные для тестирования)
if [ ! -f ssl/cert.pem ] || [ ! -f ssl/key.pem ]; then
    log "Создаем самоподписанные SSL сертификаты..."
    # Удаляем старые файлы если они существуют
    sudo rm -f ssl/cert.pem ssl/key.pem
    # Создаем новые сертификаты
    sudo openssl req -x509 -newkey rsa:4096 -keyout ssl/key.pem -out ssl/cert.pem -days 365 -nodes \
        -subj "/C=RU/ST=Moscow/L=Moscow/O=TimeTracker/CN=$DOMAIN"
    # Устанавливаем правильные права
    sudo chmod 600 ssl/key.pem
    sudo chmod 644 ssl/cert.pem
    sudo chown $USER:$USER ssl/cert.pem ssl/key.pem
    log "SSL сертификаты созданы"
else
    log "SSL сертификаты уже существуют"
    # Проверяем и исправляем права если нужно
    if [ -f ssl/key.pem ]; then
        sudo chmod 600 ssl/key.pem
        sudo chown $USER:$USER ssl/key.pem
    fi
    if [ -f ssl/cert.pem ]; then
        sudo chmod 644 ssl/cert.pem
        sudo chown $USER:$USER ssl/cert.pem
    fi
fi

# Останавливаем старые контейнеры
log "Останавливаем старые контейнеры..."
sudo docker compose down || true

# Собираем и запускаем новые контейнеры
log "Собираем и запускаем контейнеры..."
sudo docker compose up -d --build

# Ждем запуска
log "Ждем запуска приложения..."
sleep 10

# Проверяем статус
if sudo docker compose ps | grep -q "Up"; then
    log "✅ Приложение успешно запущено!"
    log "🌐 Сайт доступен по адресу: https://$DOMAIN"
    log "📊 Статус контейнеров:"
    sudo docker compose ps
else
    error "❌ Ошибка при запуске приложения. Проверьте логи: sudo docker compose logs"
fi

# Настраиваем автозапуск
log "Настраиваем автозапуск..."
sudo cp time-tracker.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME

# Создаем cron для резервного копирования
log "Настраиваем автоматическое резервное копирование..."
(crontab -l 2>/dev/null; echo "0 2 * * * cd $APP_DIR && python3 backup_db.py") | crontab -

log "🎉 Деплой завершен успешно!"
log "📝 Следующие шаги:"
log "   1. Отредактируйте .env файл с вашими настройками"
log "   2. Настройте DNS для вашего домена"
log "   3. Получите настоящие SSL сертификаты (Let's Encrypt)"
log "   4. Проверьте работу сайта"

echo ""
log "🔧 Полезные команды:"
log "   sudo docker compose logs -f          # Просмотр логов"
log "   sudo docker compose restart          # Перезапуск"
log "   sudo docker compose down             # Остановка"
log "   sudo systemctl status $SERVICE_NAME  # Статус сервиса"
