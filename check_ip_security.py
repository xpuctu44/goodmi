#!/usr/bin/env python3
"""
Скрипт для проверки настроек безопасности IP адресов
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db
from app.models import AllowedIP
from sqlalchemy.orm import Session

def check_ip_security():
    """Проверяет настройки безопасности IP адресов"""
    print("🔍 Проверка настроек безопасности IP адресов...")
    print("=" * 50)
    
    # Получаем сессию базы данных
    db = next(get_db())
    
    try:
        # Проверяем количество разрешенных IP
        allowed_ips = db.query(AllowedIP).filter(AllowedIP.is_active == True).all()
        
        print(f"📊 Найдено активных разрешенных IP адресов: {len(allowed_ips)}")
        
        if not allowed_ips:
            print("⚠️  ВНИМАНИЕ: Нет активных разрешенных IP адресов!")
            print("   Это означает, что проверка IP отключена и любой может отмечаться.")
            print("   Рекомендуется добавить разрешенные IP адреса.")
        else:
            print("\n📋 Список разрешенных IP адресов:")
            for ip in allowed_ips:
                status = "✅ Активен" if ip.is_active else "❌ Неактивен"
                print(f"   • {ip.ip_address} - {ip.description or 'Без описания'} ({status})")
        
        print("\n🔧 Как добавить разрешенные IP:")
        print("   1. Войдите как администратор")
        print("   2. Перейдите в раздел 'Разрешенные IP'")
        print("   3. Добавьте IP адреса вашей сети (например, 192.168.1.1)")
        print("   4. Система будет проверять первые 3 октета (192.168.1.x)")
        
        print("\n🌐 Примеры IP адресов для добавления:")
        print("   • 192.168.1.1 - для сети 192.168.1.x")
        print("   • 10.0.0.1 - для сети 10.0.0.x")
        print("   • 172.16.0.1 - для сети 172.16.0.x")
        
    except Exception as e:
        print(f"❌ Ошибка при проверке: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_ip_security()
