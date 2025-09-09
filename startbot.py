#!/usr/bin/env python3
"""
Скрипт для запуска Telegram бота Time Tracker
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
    print_colored("🔍 Проверка зависимостей для бота...", Colors.CYAN)
    
    try:
        import python_telegram_bot
        print_colored("✅ python-telegram-bot установлен", Colors.GREEN)
    except ImportError:
        print_colored("❌ python-telegram-bot не найден. Устанавливаю...", Colors.YELLOW)
        subprocess.run([sys.executable, "-m", "pip", "install", "python-telegram-bot"], check=True)
        print_colored("✅ python-telegram-bot установлен", Colors.GREEN)
    
    # Проверяем requirements.txt
    if Path("requirements.txt").exists():
        print_colored("📦 Устанавливаю зависимости из requirements.txt...", Colors.CYAN)
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        print_colored("✅ Зависимости установлены", Colors.GREEN)

def setup_environment():
    """Настройка окружения"""
    print_colored("⚙️ Настройка окружения для бота...", Colors.CYAN)
    
    # Проверяем наличие .env файла
    if not Path(".env").exists():
        print_colored("⚠️ Файл .env не найден. Создаю базовый...", Colors.YELLOW)
        create_env_file()
    
    # Проверяем токен бота
    from dotenv import load_dotenv
    load_dotenv()
    
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        print_colored("❌ TELEGRAM_BOT_TOKEN не найден в .env файле!", Colors.RED)
        print_colored("💡 Добавьте в .env файл:", Colors.YELLOW)
        print_colored("   TELEGRAM_BOT_TOKEN=ваш_токен_здесь", Colors.WHITE)
        print_colored("📖 Инструкция по получению токена:", Colors.CYAN)
        print_colored("   1. Напишите @BotFather в Telegram", Colors.WHITE)
        print_colored("   2. Используйте команду /newbot", Colors.WHITE)
        print_colored("   3. Следуйте инструкциям", Colors.WHITE)
        print_colored("   4. Скопируйте токен в .env файл", Colors.WHITE)
        return False
    
    print_colored("✅ Токен бота найден", Colors.GREEN)
    return True

def create_env_file():
    """Создание базового .env файла для бота"""
    env_content = """# Настройки для Telegram бота
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Настройки для продакшена
ENVIRONMENT=production
HOST=0.0.0.0
PORT=8001
DOMAIN=work.maxmobiles.ru

# База данных
DATABASE_URL=sqlite:///./time_tracker.db

# Секретный ключ
SECRET_KEY=your-secret-key-here-change-this-in-production

# Разрешенные хосты
ALLOWED_HOSTS=work.maxmobiles.ru,localhost,127.0.0.1

# Настройки логирования
LOG_LEVEL=INFO
"""
    
    with open(".env", "w", encoding="utf-8") as f:
        f.write(env_content)
    
    print_colored("📝 Создан файл .env. Добавьте токен бота!", Colors.YELLOW)

def start_bot():
    """Запуск бота"""
    print_colored("🤖 Запуск Telegram бота...", Colors.GREEN)
    print_colored("=" * 60, Colors.BLUE)
    print_colored("📱 Бот будет работать параллельно с веб-сайтом", Colors.PURPLE)
    print_colored("🛑 Для остановки нажмите Ctrl+C", Colors.YELLOW)
    print_colored("=" * 60, Colors.BLUE)
    
    try:
        # Запускаем бота
        process = subprocess.Popen([sys.executable, "bot_runner.py"])
        
        print_colored("✅ Бот запущен успешно!", Colors.GREEN)
        print_colored("📝 PID процесса: " + str(process.pid), Colors.CYAN)
        print_colored("🛑 Для остановки нажмите Ctrl+C", Colors.YELLOW)
        
        # Ожидаем завершения процесса
        process.wait()
        
    except KeyboardInterrupt:
        print_colored("\n🛑 Получен сигнал остановки...", Colors.YELLOW)
        if 'process' in locals():
            process.terminate()
            process.wait()
        print_colored("✅ Бот остановлен", Colors.GREEN)
    except Exception as e:
        print_colored(f"❌ Ошибка запуска бота: {e}", Colors.RED)
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
    print_colored("🤖 Time Tracker - Запуск Telegram бота", Colors.BOLD + Colors.GREEN)
    print_colored("📱 Домен: work.maxmobiles.ru", Colors.PURPLE)
    print_colored("=" * 60, Colors.BLUE)
    
    try:
        # Проверяем, что мы в правильной директории
        if not Path("bot_runner.py").exists():
            print_colored("❌ Файл bot_runner.py не найден!", Colors.RED)
            print_colored("💡 Убедитесь, что вы запускаете скрипт из корневой директории проекта", Colors.YELLOW)
            sys.exit(1)
        
        # Показываем статус
        show_status()
        print()
        
        # Проверяем зависимости
        check_requirements()
        print()
        
        # Настраиваем окружение
        if not setup_environment():
            print_colored("❌ Не удалось настроить окружение", Colors.RED)
            sys.exit(1)
        print()
        
        # Запускаем бота
        start_bot()
        
    except KeyboardInterrupt:
        print_colored("\n👋 До свидания!", Colors.GREEN)
    except Exception as e:
        print_colored(f"❌ Критическая ошибка: {e}", Colors.RED)
        sys.exit(1)

if __name__ == "__main__":
    main()
