#!/usr/bin/env python3
"""
Скрипт для запуска миграций базы данных
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine
from app.migrations import run_sqlite_migrations

def run_migrations():
    """Запускает миграции базы данных"""
    print("🔄 Запуск миграций базы данных...")
    print("=" * 40)
    
    try:
        run_sqlite_migrations(engine)
        print("✅ Миграции выполнены успешно!")
        
        # Проверяем, что таблица allowed_ips создана
        from sqlalchemy import text
        with engine.connect() as connection:
            result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='allowed_ips'"))
            if result.fetchone():
                print("✅ Таблица allowed_ips создана")
            else:
                print("❌ Таблица allowed_ips не найдена")
                
    except Exception as e:
        print(f"❌ Ошибка при выполнении миграций: {e}")

if __name__ == "__main__":
    run_migrations()
