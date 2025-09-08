#!/usr/bin/env python3
"""
Test script for new Telegram bot web credentials functionality
"""
import os
import sys
sys.path.append('.')

from app.database import get_db
from app.models import User
from app.routers.telegram_bot import TelegramBot
from sqlalchemy.orm import Session

def test_database_schema():
    """Test that new columns exist in database"""
    print("Testing database schema...")

    db = next(get_db())

    # Check if columns exist by trying to query them
    try:
        # This will fail if columns don't exist
        user = db.query(User).filter(User.web_username.isnot(None)).first()
        print("OK web_username column exists")

        user = db.query(User).filter(User.web_password_plain.isnot(None)).first()
        print("OK web_password_plain column exists")

    except Exception as e:
        print(f"ERROR Database schema error: {e}")
        return False

    print("OK Database schema is correct")
    return True

def test_credential_generation():
    """Test credential generation function"""
    print("\nTesting credential generation...")

    bot = TelegramBot()

    # Test with a sample name
    username, password = bot._generate_web_credentials("Иван Иванов")

    print(f"Generated username: {username}")
    print(f"Generated password: {password}")

    # Check username format
    if username and len(username) > 0:
        print("OK Username generated successfully")
    else:
        print("ERROR Username generation failed")
        return False

    # Check password format
    if password and len(password) >= 8:
        print("OK Password generated successfully")
    else:
        print("ERROR Password generation failed")
        return False

    print("OK Credential generation works correctly")
    return True

def test_user_creation():
    """Test creating a user with web credentials"""
    print("\nTesting user creation with web credentials...")

    db = next(get_db())
    bot = TelegramBot()

    # Generate credentials
    username, password = bot._generate_web_credentials("Тестовый Пользователь")

    # Create test user
    test_user = User(
        email=f"{username}@web.local",
        full_name="Тестовый Пользователь",
        password_hash="test_hash",  # We don't need real hash for this test
        role="employee",
        is_active=True,
        web_username=username,
        web_password_plain=password
    )

    try:
        db.add(test_user)
        db.commit()
        db.refresh(test_user)

        print(f"OK User created with ID: {test_user.id}")
        print(f"OK Web username: {test_user.web_username}")
        print(f"OK Web password: {test_user.web_password_plain}")
        print(f"OK Email: {test_user.email}")

        # Clean up test user
        db.delete(test_user)
        db.commit()

        print("OK Test user cleaned up")
        return True

    except Exception as e:
        db.rollback()
        print(f"ERROR User creation failed: {e}")
        return False

def main():
    print("Testing new Telegram bot web credentials functionality\n")

    success = True

    success &= test_database_schema()
    success &= test_credential_generation()
    success &= test_user_creation()

    if success:
        print("\nSUCCESS All tests passed! New functionality is working correctly.")
    else:
        print("\nFAILED Some tests failed. Please check the implementation.")

    return success

if __name__ == "__main__":
    main()