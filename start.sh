#!/bin/bash

# Скрипт для быстрого запуска Time Tracker
# Домен: work.maxmobiles.ru

echo "🕐 Запуск Time Tracker на work.maxmobiles.ru"
echo "=============================================="

# Проверяем Python
if command -v python3 &> /dev/null; then
    echo "✅ Python3 найден"
    python3 startmysite.py
elif command -v python &> /dev/null; then
    echo "✅ Python найден"
    python startmysite.py
else
    echo "❌ Python не найден! Установите Python 3.7+"
    exit 1
fi
