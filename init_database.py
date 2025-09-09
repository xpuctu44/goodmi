#!/usr/bin/env python3
"""
Скрипт для полной инициализации базы данных
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base
from app import models
from app.migrations import run_sqlite_migrations

def init_database():
    """Инициализирует базу данных"""
    print("🚀 Инициализация базы данных...")
    print("=" * 40)
    
    try:
        # Создаем все таблицы
        print("📋 Создание таблиц...")
        Base.metadata.create_all(bind=engine)
        print("✅ Таблицы созданы")
        
        # Запускаем миграции
        print("🔄 Выполнение миграций...")
        run_sqlite_migrations(engine)
        print("✅ Миграции выполнены")
        
        # Проверяем созданные таблицы
        from sqlalchemy import text
        with engine.connect() as connection:
            result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result.fetchall()]
            
        print(f"\n📊 Созданные таблицы: {', '.join(tables)}")
        
        if 'allowed_ips' in tables:
            print("✅ Таблица allowed_ips создана - проверка IP будет работать")
        else:
            print("❌ Таблица allowed_ips не создана")
            
    except Exception as e:
        print(f"❌ Ошибка при инициализации: {e}")

if __name__ == "__main__":
    init_database()
