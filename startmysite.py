#!/usr/bin/env python3
"""
Скрипт для запуска Time Tracker на выделенном сервере
Домен: work.maxmobiles.ru
"""

import os
import sys
import subprocess
import signal
import time
from pathlib import Path

# Цвета для вывода в консоль
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_colored(text, color=Colors.WHITE):
    """Печать цветного текста"""
    print(f"{color}{text}{Colors.END}")

def check_requirements():
    """Проверка зависимостей"""
    print_colored("🔍 Проверка зависимостей...", Colors.CYAN)
    
    try:
        import uvicorn
        print_colored("✅ uvicorn установлен", Colors.GREEN)
    except ImportError:
        print_colored("❌ uvicorn не найден. Устанавливаю...", Colors.YELLOW)
        subprocess.run([sys.executable, "-m", "pip", "install", "uvicorn[standard]"], check=True)
        print_colored("✅ uvicorn установлен", Colors.GREEN)
    
    # Проверяем requirements.txt
    if Path("requirements.txt").exists():
        print_colored("📦 Устанавливаю зависимости из requirements.txt...", Colors.CYAN)
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print_colored("✅ Зависимости установлены", Colors.GREEN)

def setup_environment():
    """Настройка окружения"""
    print_colored("⚙️ Настройка окружения...", Colors.CYAN)
    
    # Устанавливаем переменные окружения для продакшена
    os.environ.setdefault("ENVIRONMENT", "production")
    os.environ.setdefault("HOST", "0.0.0.0")
    os.environ.setdefault("PORT", "8001")
    os.environ.setdefault("DOMAIN", "work.maxmobiles.ru")
    
    # Проверяем наличие .env файла
    if not Path(".env").exists():
        print_colored("⚠️ Файл .env не найден. Создаю базовый...", Colors.YELLOW)
        create_env_file()
    
    print_colored("✅ Окружение настроено", Colors.GREEN)

def create_env_file():
    """Создание базового .env файла"""
    env_content = """# Настройки для продакшена
ENVIRONMENT=production
HOST=0.0.0.0
PORT=8001
DOMAIN=work.maxmobiles.ru

# База данных (настройте под вашу БД)
DATABASE_URL=sqlite:///./time_tracker.db

# Секретный ключ (сгенерируйте новый для продакшена)
SECRET_KEY=your-secret-key-here-change-this-in-production

# Настройки безопасности
ALLOWED_HOSTS=work.maxmobiles.ru,localhost,127.0.0.1

# Настройки логирования
LOG_LEVEL=INFO
"""
    
    with open(".env", "w", encoding="utf-8") as f:
        f.write(env_content)
    
    print_colored("📝 Создан файл .env. Отредактируйте его под ваши настройки!", Colors.YELLOW)

def start_server():
    """Запуск сервера"""
    print_colored("🚀 Запуск Time Tracker сервера...", Colors.GREEN)
    print_colored("=" * 60, Colors.BLUE)
    print_colored("🌐 Домен: work.maxmobiles.ru", Colors.PURPLE)
    print_colored("🔗 Локальный доступ: http://localhost:8001", Colors.CYAN)
    print_colored("📊 Админ панель: http://localhost:8001/admin", Colors.CYAN)
    print_colored("=" * 60, Colors.BLUE)
    
    # Параметры запуска для продакшена
    uvicorn_args = [
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8001",
        "--workers", "4",  # Количество воркеров для продакшена
        "--access-log",
        "--log-level", "info",
        "--timeout-keep-alive", "30",
        "--limit-concurrency", "1000",
        "--limit-max-requests", "1000"
    ]
    
    try:
        # Запускаем сервер
        process = subprocess.Popen(uvicorn_args)
        
        print_colored("✅ Сервер запущен успешно!", Colors.GREEN)
        print_colored("📝 PID процесса:", Colors.CYAN, end=" ")
        print_colored(str(process.pid), Colors.WHITE)
        print_colored("🛑 Для остановки нажмите Ctrl+C", Colors.YELLOW)
        
        # Ожидаем завершения процесса
        process.wait()
        
    except KeyboardInterrupt:
        print_colored("\n🛑 Получен сигнал остановки...", Colors.YELLOW)
        if 'process' in locals():
            process.terminate()
            process.wait()
        print_colored("✅ Сервер остановлен", Colors.GREEN)
    except Exception as e:
        print_colored(f"❌ Ошибка запуска сервера: {e}", Colors.RED)
        sys.exit(1)

def show_status():
    """Показать статус системы"""
    print_colored("📊 Статус системы:", Colors.CYAN)
    print_colored(f"🐍 Python версия: {sys.version}", Colors.WHITE)
    print_colored(f"📁 Рабочая директория: {os.getcwd()}", Colors.WHITE)
    print_colored(f"🌐 Домен: {os.environ.get('DOMAIN', 'work.maxmobiles.ru')}", Colors.WHITE)
    print_colored(f"🔧 Окружение: {os.environ.get('ENVIRONMENT', 'production')}", Colors.WHITE)

def main():
    """Основная функция"""
    print_colored("=" * 60, Colors.BLUE)
    print_colored("🕐 Time Tracker - Запуск на продакшен сервере", Colors.BOLD + Colors.GREEN)
    print_colored("🌐 Домен: work.maxmobiles.ru", Colors.PURPLE)
    print_colored("=" * 60, Colors.BLUE)
    
    try:
        # Проверяем, что мы в правильной директории
        if not Path("app/main.py").exists():
            print_colored("❌ Файл app/main.py не найден!", Colors.RED)
            print_colored("💡 Убедитесь, что вы запускаете скрипт из корневой директории проекта", Colors.YELLOW)
            sys.exit(1)
        
        # Показываем статус
        show_status()
        print()
        
        # Проверяем зависимости
        check_requirements()
        print()
        
        # Настраиваем окружение
        setup_environment()
        print()
        
        # Запускаем сервер
        start_server()
        
    except KeyboardInterrupt:
        print_colored("\n👋 До свидания!", Colors.GREEN)
    except Exception as e:
        print_colored(f"❌ Критическая ошибка: {e}", Colors.RED)
        sys.exit(1)

if __name__ == "__main__":
    main()
