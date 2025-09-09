#!/usr/bin/env python3
"""
Универсальный скрипт для запуска Time Tracker (сайт + бот)
"""

import os
import sys
import subprocess
import signal
import time
import threading
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
        import python_telegram_bot
        print_colored("✅ Все зависимости установлены", Colors.GREEN)
    except ImportError as e:
        print_colored(f"❌ Отсутствует зависимость: {e}", Colors.YELLOW)
        print_colored("📦 Устанавливаю зависимости...", Colors.CYAN)
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print_colored("✅ Зависимости установлены", Colors.GREEN)

def setup_environment():
    """Настройка окружения"""
    print_colored("⚙️ Настройка окружения...", Colors.CYAN)
    
    # Устанавливаем переменные окружения
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

# База данных
DATABASE_URL=sqlite:///./time_tracker.db

# Секретный ключ (ОБЯЗАТЕЛЬНО измените!)
SECRET_KEY=your-super-secret-key-change-this-in-production

# Разрешенные хосты
ALLOWED_HOSTS=work.maxmobiles.ru,localhost,127.0.0.1

# Настройки логирования
LOG_LEVEL=INFO

# Telegram бот (добавьте токен)
TELEGRAM_BOT_TOKEN=your_bot_token_here
"""
    
    with open(".env", "w", encoding="utf-8") as f:
        f.write(env_content)
    
    print_colored("📝 Создан файл .env. Настройте токен бота!", Colors.YELLOW)

def start_website():
    """Запуск веб-сайта"""
    print_colored("🌐 Запуск веб-сайта...", Colors.GREEN)
    
    uvicorn_args = [
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8001",
        "--workers", "4",
        "--access-log",
        "--log-level", "info"
    ]
    
    try:
        process = subprocess.Popen(uvicorn_args)
        print_colored("✅ Веб-сайт запущен на http://localhost:8001", Colors.GREEN)
        return process
    except Exception as e:
        print_colored(f"❌ Ошибка запуска веб-сайта: {e}", Colors.RED)
        return None

def start_bot():
    """Запуск Telegram бота"""
    print_colored("🤖 Запуск Telegram бота...", Colors.GREEN)
    
    try:
        process = subprocess.Popen([sys.executable, "bot_runner.py"])
        print_colored("✅ Telegram бот запущен", Colors.GREEN)
        return process
    except Exception as e:
        print_colored(f"❌ Ошибка запуска бота: {e}", Colors.RED)
        return None

def main():
    """Основная функция"""
    print_colored("=" * 70, Colors.BLUE)
    print_colored("🚀 Time Tracker - Запуск полной системы", Colors.BOLD + Colors.GREEN)
    print_colored("🌐 Домен: work.maxmobiles.ru", Colors.PURPLE)
    print_colored("=" * 70, Colors.BLUE)
    
    try:
        # Проверяем, что мы в правильной директории
        if not Path("app/main.py").exists():
            print_colored("❌ Файл app/main.py не найден!", Colors.RED)
            print_colored("💡 Убедитесь, что вы запускаете скрипт из корневой директории проекта", Colors.YELLOW)
            sys.exit(1)
        
        # Проверяем зависимости
        check_requirements()
        print()
        
        # Настраиваем окружение
        setup_environment()
        print()
        
        # Запускаем веб-сайт
        website_process = start_website()
        if not website_process:
            sys.exit(1)
        
        # Небольшая пауза для запуска сайта
        time.sleep(2)
        
        # Запускаем бота
        bot_process = start_bot()
        if not bot_process:
            print_colored("⚠️ Бот не запущен, но сайт работает", Colors.YELLOW)
        
        print_colored("=" * 70, Colors.BLUE)
        print_colored("🎉 Система запущена успешно!", Colors.BOLD + Colors.GREEN)
        print_colored("🌐 Веб-сайт: http://localhost:8001", Colors.CYAN)
        print_colored("📊 Админ панель: http://localhost:8001/admin", Colors.CYAN)
        if bot_process:
            print_colored("🤖 Telegram бот: активен", Colors.CYAN)
        print_colored("🛑 Для остановки нажмите Ctrl+C", Colors.YELLOW)
        print_colored("=" * 70, Colors.BLUE)
        
        # Ожидаем завершения процессов
        try:
            while True:
                time.sleep(1)
                # Проверяем, что процессы еще работают
                if website_process.poll() is not None:
                    print_colored("❌ Веб-сайт остановлен", Colors.RED)
                    break
                if bot_process and bot_process.poll() is not None:
                    print_colored("❌ Telegram бот остановлен", Colors.RED)
                    break
        except KeyboardInterrupt:
            print_colored("\n🛑 Получен сигнал остановки...", Colors.YELLOW)
            
            # Останавливаем процессы
            if website_process:
                website_process.terminate()
                website_process.wait()
                print_colored("✅ Веб-сайт остановлен", Colors.GREEN)
            
            if bot_process:
                bot_process.terminate()
                bot_process.wait()
                print_colored("✅ Telegram бот остановлен", Colors.GREEN)
            
            print_colored("👋 Система остановлена", Colors.GREEN)
        
    except Exception as e:
        print_colored(f"❌ Критическая ошибка: {e}", Colors.RED)
        sys.exit(1)

if __name__ == "__main__":
    main()
