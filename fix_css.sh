#!/bin/bash

echo "🔧 Исправление проблемы с CSS стилями..."

# Останавливаем контейнеры
echo "⏹️  Останавливаем контейнеры..."
docker-compose down

# Пересобираем образы
echo "🔨 Пересобираем образы..."
docker-compose build --no-cache

# Запускаем контейнеры
echo "🚀 Запускаем контейнеры..."
docker-compose up -d

# Проверяем статус
echo "📊 Проверяем статус контейнеров..."
docker-compose ps

# Проверяем логи nginx
echo "📝 Проверяем логи nginx..."
docker-compose logs nginx

echo "✅ Готово! Проверьте ваш сайт."
echo "💡 Если проблема остается, проверьте:"
echo "   1. Доступность файла /app/app/static/css/styles.css в контейнере nginx"
echo "   2. Логи nginx: docker-compose logs nginx"
echo "   3. Логи web: docker-compose logs web"
