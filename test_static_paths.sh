#!/bin/bash

echo "🔍 Проверка путей к статическим файлам в контейнерах..."
echo "======================================================"

# Проверяем структуру в web контейнере
echo "📁 Структура в web контейнере:"
docker-compose exec web ls -la /app/ || echo "Web контейнер не запущен"

echo ""
echo "📁 Структура в nginx контейнере:"
docker-compose exec nginx ls -la /app/ || echo "Nginx контейнер не запущен"

echo ""
echo "📁 Проверяем монтирование статических файлов в nginx:"
docker-compose exec nginx ls -la /app/app/static/ || echo "Путь /app/app/static/ не найден"

echo ""
echo "📁 Проверяем альтернативный путь:"
docker-compose exec nginx ls -la /app/static/ || echo "Путь /app/static/ не найден"

echo ""
echo "🔧 Текущая конфигурация nginx:"
echo "   location /static/ {"
echo "       alias /app/app/static/;"
echo "   }"
