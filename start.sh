#!/bin/bash

# Скрипт для быстрого запуска Time Tracker
# Домен: work.maxmobiles.ru

echo "🕐 Time Tracker - Выберите режим запуска"
echo "=============================================="
echo "1) 🌐 Только веб-сайт"
echo "2) 🤖 Только Telegram бот"
echo "3) 🚀 Полная система (сайт + бот)"
echo "=============================================="

read -p "Выберите вариант (1-3): " choice

# Проверяем Python
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ Python не найден! Установите Python 3.7+"
    exit 1
fi

case $choice in
    1)
        echo "🌐 Запуск веб-сайта..."
        $PYTHON_CMD startmysite.py
        ;;
    2)
        echo "🤖 Запуск Telegram бота..."
        $PYTHON_CMD startbot.py
        ;;
    3)
        echo "🚀 Запуск полной системы..."
        $PYTHON_CMD startall.py
        ;;
    *)
        echo "❌ Неверный выбор. Запускаю веб-сайт по умолчанию..."
        $PYTHON_CMD startmysite.py
        ;;
esac
