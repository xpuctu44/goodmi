#!/usr/bin/env python3
"""
🚀 Cloud Deployment Script для Time Tracker
Автоматический запуск сайта и Telegram бота на облачном сервере

Особенности:
- Параллельный запуск веб-сервера и бота
- Автоматический перезапуск при падении
- Мониторинг состояния процессов
- Health checks
- Детальное логирование
- Graceful shutdown
"""

import os
import sys
import subprocess
import signal
import time
import threading
import logging
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('cloud_deploy.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class CloudDeployer:
    """Класс для управления развертыванием на облачном сервере"""

    def __init__(self):
        self.website_process: Optional[subprocess.Popen] = None
        self.bot_process: Optional[subprocess.Popen] = None
        self.monitoring_thread: Optional[threading.Thread] = None
        self.running = False
        self.restart_count = {"website": 0, "bot": 0}
        self.max_restarts = 5
        self.restart_window = timedelta(minutes=5)

        # Настройки
        self.config = {
            "website_port": int(os.getenv("PORT", "8001")),
            "website_host": os.getenv("HOST", "0.0.0.0"),
            "domain": os.getenv("DOMAIN", "localhost"),
            "health_check_interval": 30,  # секунд
            "max_restart_attempts": 5,
            "restart_delay": 10,  # секунд
        }

    def setup_environment(self) -> bool:
        """Настройка окружения для облачного сервера"""
        logger.info("🔧 Настройка окружения для облачного сервера...")

        try:
            # Проверяем наличие необходимых файлов
            required_files = ["app/main.py", "bot_runner.py", "requirements.txt"]
            for file_path in required_files:
                if not Path(file_path).exists():
                    logger.error(f"❌ Не найден файл: {file_path}")
                    return False

            # Устанавливаем переменные окружения для продакшена
            os.environ.setdefault("ENVIRONMENT", "production")
            os.environ.setdefault("HOST", self.config["website_host"])
            os.environ.setdefault("PORT", str(self.config["website_port"]))
            os.environ.setdefault("DOMAIN", self.config["domain"])

            # Проверяем наличие .env файла
            if not Path(".env").exists():
                logger.warning("⚠️ Файл .env не найден. Создаю базовый...")
                self.create_env_file()

            # Проверяем токен бота
            bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
            if not bot_token:
                logger.error("❌ TELEGRAM_BOT_TOKEN не найден в переменных окружения!")
                logger.info("💡 Добавьте TELEGRAM_BOT_TOKEN в переменные окружения или .env файл")
                return False

            logger.info("✅ Окружение настроено успешно")
            return True

        except Exception as e:
            logger.error(f"❌ Ошибка настройки окружения: {e}")
            return False

    def create_env_file(self):
        """Создание базового .env файла для облака"""
        env_content = f"""# Настройки для облачного сервера
ENVIRONMENT=production
HOST={self.config["website_host"]}
PORT={self.config["website_port"]}
DOMAIN={self.config["domain"]}

# База данных (SQLite для простоты, можно заменить на PostgreSQL)
DATABASE_URL=sqlite:///./time_tracker.db

# Секретный ключ (ОБЯЗАТЕЛЬНО измените!)
SECRET_KEY={os.urandom(32).hex()}

# Разрешенные хосты
ALLOWED_HOSTS={self.config["domain"]},localhost,127.0.0.1

# Настройки логирования
LOG_LEVEL=INFO

# Telegram бот (добавьте токен!)
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Настройки для облака
CLOUD_DEPLOYMENT=true
HEALTH_CHECK_ENABLED=true
AUTO_RESTART=true
"""

        with open(".env", "w", encoding="utf-8") as f:
            f.write(env_content)

        logger.info("📝 Создан файл .env для облачного сервера")

    def install_dependencies(self) -> bool:
        """Установка зависимостей"""
        logger.info("📦 Установка зависимостей...")

        try:
            # Обновляем pip
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"],
                         check=True, capture_output=True)

            # Устанавливаем зависимости
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
                         check=True, capture_output=True)

            logger.info("✅ Зависимости установлены успешно")
            return True

        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Ошибка установки зависимостей: {e}")
            return False

    def start_website(self) -> bool:
        """Запуск веб-сервера"""
        logger.info("🌐 Запуск веб-сервера...")

        try:
            uvicorn_args = [
                sys.executable, "-m", "uvicorn",
                "app.main:app",
                "--host", self.config["website_host"],
                "--port", str(self.config["website_port"]),
                "--workers", "2",  # Для облака используем меньше воркеров
                "--access-log",
                "--log-level", "info",
                "--timeout-keep-alive", "30",
                "--limit-concurrency", "100",
                "--limit-max-requests", "500"
            ]

            self.website_process = subprocess.Popen(
                uvicorn_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Ждем немного для запуска
            time.sleep(3)

            if self.website_process.poll() is None:
                logger.info(f"✅ Веб-сервер запущен на http://{self.config['website_host']}:{self.config['website_port']}")
                return True
            else:
                stdout, stderr = self.website_process.communicate()
                logger.error(f"❌ Веб-сервер не запустился: {stderr}")
                return False

        except Exception as e:
            logger.error(f"❌ Ошибка запуска веб-сервера: {e}")
            return False

    def start_bot(self) -> bool:
        """Запуск Telegram бота"""
        logger.info("🤖 Запуск Telegram бота...")

        try:
            self.bot_process = subprocess.Popen(
                [sys.executable, "bot_runner.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Ждем немного для запуска
            time.sleep(2)

            if self.bot_process.poll() is None:
                logger.info("✅ Telegram бот запущен")
                return True
            else:
                stdout, stderr = self.bot_process.communicate()
                logger.error(f"❌ Бот не запустился: {stderr}")
                return False

        except Exception as e:
            logger.error(f"❌ Ошибка запуска бота: {e}")
            return False

    def health_check_website(self) -> bool:
        """Проверка здоровья веб-сервера"""
        try:
            url = f"http://localhost:{self.config['website_port']}/health"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except:
            return False

    def health_check_bot(self) -> bool:
        """Проверка здоровья бота (проверка процесса)"""
        if self.bot_process and self.bot_process.poll() is None:
            return True
        return False

    def restart_service(self, service_name: str) -> bool:
        """Перезапуск сервиса"""
        logger.warning(f"🔄 Перезапуск {service_name}...")

        # Проверяем лимит перезапусков
        if self.restart_count[service_name] >= self.max_restarts:
            logger.error(f"❌ Превышен лимит перезапусков для {service_name}")
            return False

        self.restart_count[service_name] += 1

        # Останавливаем процесс
        if service_name == "website" and self.website_process:
            self.website_process.terminate()
            self.website_process.wait()
            time.sleep(2)
            return self.start_website()
        elif service_name == "bot" and self.bot_process:
            self.bot_process.terminate()
            self.bot_process.wait()
            time.sleep(2)
            return self.start_bot()

        return False

    def monitoring_loop(self):
        """Цикл мониторинга состояния сервисов"""
        logger.info("👀 Запуск мониторинга сервисов...")

        while self.running:
            try:
                # Проверяем веб-сервер
                if not self.health_check_website():
                    logger.warning("⚠️ Веб-сервер не отвечает на health check")
                    if not self.restart_service("website"):
                        logger.error("❌ Не удалось перезапустить веб-сервер")
                else:
                    # Сбрасываем счетчик перезапусков при успешной проверке
                    self.restart_count["website"] = 0

                # Проверяем бота
                if not self.health_check_bot():
                    logger.warning("⚠️ Telegram бот не работает")
                    if not self.restart_service("bot"):
                        logger.error("❌ Не удалось перезапустить бота")
                else:
                    # Сбрасываем счетчик перезапусков при успешной проверке
                    self.restart_count["bot"] = 0

                time.sleep(self.config["health_check_interval"])

            except Exception as e:
                logger.error(f"❌ Ошибка в цикле мониторинга: {e}")
                time.sleep(5)

    def start_monitoring(self):
        """Запуск потока мониторинга"""
        self.monitoring_thread = threading.Thread(target=self.monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("✅ Мониторинг запущен")

    def stop_services(self):
        """Остановка всех сервисов"""
        logger.info("🛑 Остановка сервисов...")

        self.running = False

        # Останавливаем веб-сервер
        if self.website_process:
            try:
                self.website_process.terminate()
                self.website_process.wait(timeout=10)
                logger.info("✅ Веб-сервер остановлен")
            except:
                self.website_process.kill()
                logger.info("⚠️ Веб-сервер принудительно остановлен")

        # Останавливаем бота
        if self.bot_process:
            try:
                self.bot_process.terminate()
                self.bot_process.wait(timeout=10)
                logger.info("✅ Telegram бот остановлен")
            except:
                self.bot_process.kill()
                logger.info("⚠️ Telegram бот принудительно остановлен")

    def show_status(self):
        """Показать статус системы"""
        logger.info("=" * 60)
        logger.info("📊 СТАТУС СИСТЕМЫ TIME TRACKER")
        logger.info("=" * 60)
        logger.info(f"🌐 Веб-сервер: {'✅ Активен' if self.website_process and self.website_process.poll() is None else '❌ Остановлен'}")
        logger.info(f"🤖 Telegram бот: {'✅ Активен' if self.bot_process and self.bot_process.poll() is None else '❌ Остановлен'}")
        logger.info(f"👀 Мониторинг: {'✅ Активен' if self.monitoring_thread and self.monitoring_thread.is_alive() else '❌ Остановлен'}")
        logger.info(f"🔄 Перезапуски веб-сервера: {self.restart_count['website']}")
        logger.info(f"🔄 Перезапуски бота: {self.restart_count['bot']}")
        logger.info(f"🌐 URL: http://{self.config['domain']}:{self.config['website_port']}")
        logger.info(f"📊 Админ панель: http://{self.config['domain']}:{self.config['website_port']}/admin")
        logger.info("=" * 60)

    def run(self):
        """Основной цикл работы"""
        logger.info("🚀 Запуск Time Tracker на облачном сервере...")
        logger.info(f"🌐 Домен: {self.config['domain']}")
        logger.info(f"🔌 Порт: {self.config['website_port']}")

        try:
            # Настройка окружения
            if not self.setup_environment():
                return

            # Установка зависимостей
            if not self.install_dependencies():
                return

            # Запуск веб-сервера
            if not self.start_website():
                return

            # Запуск бота
            if not self.start_bot():
                logger.warning("⚠️ Бот не запустился, но веб-сервер работает")

            # Запуск мониторинга
            self.running = True
            self.start_monitoring()

            # Показываем статус
            self.show_status()

            logger.info("🎉 Система запущена успешно!")
            logger.info("🛑 Для остановки нажмите Ctrl+C")

            # Основной цикл
            while self.running:
                try:
                    time.sleep(1)

                    # Периодически показываем статус
                    if int(time.time()) % 300 == 0:  # Каждые 5 минут
                        self.show_status()

                except KeyboardInterrupt:
                    logger.info("\n🛑 Получен сигнал остановки...")
                    break

        except Exception as e:
            logger.error(f"❌ Критическая ошибка: {e}")
        finally:
            self.stop_services()
            logger.info("👋 Система остановлена")

def main():
    """Точка входа"""
    # Настройка обработки сигналов
    def signal_handler(signum, frame):
        logger.info(f"\n📡 Получен сигнал {signum}. Завершение работы...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Запуск деплоера
    deployer = CloudDeployer()
    deployer.run()

if __name__ == "__main__":
    main()