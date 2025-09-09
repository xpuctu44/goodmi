#!/usr/bin/env python3
"""
Скрипт для добавления тестового IP адреса
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db
from app.models import AllowedIP
from datetime import datetime, timezone, timedelta

def _get_moscow_time():
    """Получает московское время"""
    moscow_tz = timezone(timedelta(hours=3))
    return datetime.now(moscow_tz)

def add_test_ip():
    """Добавляет тестовый IP адрес"""
    print("🔧 Добавление тестового IP адреса...")
    print("=" * 40)
    
    # Получаем сессию базы данных
    db = next(get_db())
    
    try:
        # Проверяем, есть ли уже тестовый IP
        existing = db.query(AllowedIP).filter(AllowedIP.ip_address == "192.168.1.1").first()
        if existing:
            print("ℹ️  Тестовый IP 192.168.1.1 уже существует")
            return
        
        # Создаем тестовый IP
        test_ip = AllowedIP(
            ip_address="192.168.1.1",
            description="Тестовая сеть (192.168.1.x)",
            is_active=True,
            created_at=_get_moscow_time(),
            created_by=None  # Системный IP
        )
        
        db.add(test_ip)
        db.commit()
        
        print("✅ Тестовый IP адрес 192.168.1.1 добавлен")
        print("   Теперь проверка IP будет работать для сети 192.168.1.x")
        print("   Для отключения проверки удалите все IP адреса из админки")
        
    except Exception as e:
        print(f"❌ Ошибка при добавлении IP: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_test_ip()
