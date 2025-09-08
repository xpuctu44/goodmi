import logging
import os
from datetime import datetime
from pathlib import Path

def setup_logging():
    """Настройка логирования для приложения"""
    
    # Создаем директорию для логов
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Настройки логирования
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_file = os.getenv("LOG_FILE", "logs/app.log")
    
    # Формат логов
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Настройка root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        datefmt=date_format,
        handlers=[
            # Файловый логгер
            logging.FileHandler(log_file, encoding='utf-8'),
            # Консольный логгер
            logging.StreamHandler()
        ]
    )
    
    # Настройка логгеров для разных компонентов
    loggers = {
        'app': logging.getLogger('app'),
        'app.routers': logging.getLogger('app.routers'),
        'app.database': logging.getLogger('app.database'),
        'uvicorn': logging.getLogger('uvicorn'),
        'uvicorn.access': logging.getLogger('uvicorn.access'),
    }
    
    # Настройка уровня для каждого логгера
    for logger_name, logger in loggers.items():
        logger.setLevel(getattr(logging, log_level.upper()))
    
    return logging.getLogger('app')

def get_logger(name: str) -> logging.Logger:
    """Получить логгер для конкретного модуля"""
    return logging.getLogger(f'app.{name}')

# Создаем логгер для использования в приложении
logger = setup_logging()
