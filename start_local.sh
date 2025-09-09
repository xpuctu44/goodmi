#!/bin/bash

echo "🚀 Запуск локального тестирования Time Tracker..."
echo "================================================"

# Проверяем Python
echo "🐍 Проверка Python..."
python3 --version

# Устанавливаем зависимости
echo "📦 Установка зависимостей..."
pip3 install -r requirements.txt

# Создаем директорию для данных
echo "📁 Создание директории для данных..."
mkdir -p data

# Инициализируем базу данных
echo "🗄️  Инициализация базы данных..."
python3 init_database.py

# Создаем тестового пользователя
echo "👤 Создание тестового пользователя..."
python3 create_test_user.py

# Добавляем тестовый IP
echo "🔒 Настройка IP безопасности..."
python3 add_test_ip.py

# Проверяем настройки
echo "🔍 Проверка настроек..."
python3 check_ip_security.py

echo ""
echo "✅ Настройка завершена!"
echo ""
echo "🌐 Сайт доступен по адресу:"
echo "   http://localhost:8000"
echo ""
echo "👤 Тестовый пользователь:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "🚀 Для запуска сервера выполните:"
echo "   python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
echo ""
echo "🔍 Для тестирования IP проверки:"
echo "   python3 test_ip_check.py"
echo ""
echo "📋 Отчет о тестировании:"
echo "   cat local_test_report.md"
