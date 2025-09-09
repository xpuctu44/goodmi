#!/bin/bash

echo "🎨 Исправление путей к CSS стилям..."
echo "===================================="

echo "🔧 Что было исправлено:"
echo "   • Изменен путь в nginx.conf: /app/app/static/ → /app/static/"
echo "   • Изменен путь в docker-compose.yml: /app/app/static → /app/static"
echo "   • Обновлен домен: yourdomain.com → work.maxmobiles.ru"

echo ""
echo "📋 Текущая конфигурация:"
echo "   • CSS файл: /app/static/css/styles.css"
echo "   • URL: http://work.maxmobiles.ru/static/css/styles.css"
echo "   • Nginx location: /static/ → /app/static/"

echo ""
echo "🚀 Для применения изменений выполните:"
echo "   docker-compose down"
echo "   docker-compose build --no-cache"
echo "   docker-compose up -d"

echo ""
echo "🔍 Для проверки CSS доступности:"
echo "   curl -I http://work.maxmobiles.ru/static/css/styles.css"

echo ""
echo "✅ Готово! CSS стили теперь должны загружаться по правильному пути."
