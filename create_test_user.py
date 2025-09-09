#!/usr/bin/env python3
"""
Скрипт для создания тестового пользователя
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db
from app.models import User
from app.security import hash_password
from datetime import datetime, timezone, timedelta

def _get_moscow_time():
    """Получает московское время"""
    moscow_tz = timezone(timedelta(hours=3))
    return datetime.now(moscow_tz)

def create_test_user():
    """Создает тестового пользователя"""
    print("👤 Создание тестового пользователя...")
    print("=" * 40)
    
    # Получаем сессию базы данных
    db = next(get_db())
    
    try:
        # Проверяем, есть ли уже тестовый пользователь
        existing = db.query(User).filter(User.web_username == "admin").first()
        if existing:
            print("ℹ️  Тестовый пользователь admin уже существует")
            print(f"   ID: {existing.id}")
            print(f"   Email: {existing.email}")
            print(f"   Role: {existing.role}")
            return
        
        # Создаем тестового пользователя
        test_user = User(
            email="admin@test.com",
            web_username="admin",
            web_password_plain="admin123",  # Пароль в открытом виде для тестирования
            password_hash=hash_password("admin123"),
            full_name="Администратор",
            role="admin",
            is_active=True
        )
        
        db.add(test_user)
        db.commit()
        
        print("✅ Тестовый пользователь создан:")
        print("   Username: admin")
        print("   Password: admin123")
        print("   Email: admin@test.com")
        print("   Role: admin")
        print("")
        print("🔗 Для входа используйте:")
        print("   http://localhost:8000/login")
        
    except Exception as e:
        print(f"❌ Ошибка при создании пользователя: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()
