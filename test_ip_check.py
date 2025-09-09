#!/usr/bin/env python3
"""
Скрипт для тестирования проверки IP адресов
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db
from app.routers.attendance import _check_ip_allowed
from fastapi import Request
from unittest.mock import Mock

def test_ip_check():
    """Тестирует проверку IP адресов"""
    print("🔍 Тестирование проверки IP адресов...")
    print("=" * 50)
    
    # Получаем сессию базы данных
    db = next(get_db())
    
    # Создаем мок-объект Request
    def create_mock_request(ip_address):
        request = Mock()
        request.client.host = ip_address
        request.headers = {}
        return request
    
    # Тестовые IP адреса
    test_cases = [
        ("192.168.1.100", True, "IP из разрешенной сети 192.168.1.x"),
        ("192.168.1.50", True, "IP из разрешенной сети 192.168.1.x"),
        ("192.168.1.1", True, "Точный IP из разрешенной сети"),
        ("192.168.2.100", False, "IP из другой сети 192.168.2.x"),
        ("10.0.0.1", False, "IP из другой сети 10.0.0.x"),
        ("127.0.0.1", False, "Локальный IP"),
        ("8.8.8.8", False, "Внешний IP"),
    ]
    
    print("📋 Результаты тестирования:")
    print()
    
    for ip, expected, description in test_cases:
        request = create_mock_request(ip)
        result = _check_ip_allowed(request, db)
        status = "✅ РАЗРЕШЕН" if result else "❌ ЗАБЛОКИРОВАН"
        expected_status = "✅ РАЗРЕШЕН" if expected else "❌ ЗАБЛОКИРОВАН"
        
        print(f"IP: {ip:<15} | {status:<15} | {description}")
        
        if result == expected:
            print(f"   ✅ Ожидаемо: {expected_status}")
        else:
            print(f"   ❌ ОШИБКА: Ожидалось {expected_status}, получено {status}")
        print()
    
    print("🔧 Текущие настройки:")
    print("   • Разрешенная сеть: 192.168.1.x")
    print("   • Проверка работает по первым 3 октетам")
    print("   • Для отключения проверки удалите все IP из базы данных")

if __name__ == "__main__":
    test_ip_check()
