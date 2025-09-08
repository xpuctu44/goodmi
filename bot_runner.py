#!/usr/bin/env python3
"""
Telegram Bot Runner для системы учета рабочего времени
"""
import os
import asyncio
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

from app.routers.telegram_bot import telegram_bot

def main():
    # Получаем токен бота из переменных окружения
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not bot_token:
        print("TELEGRAM_BOT_TOKEN not found in environment variables")
        print("Create .env file and add TELEGRAM_BOT_TOKEN=your_token")
        print("\nHow to get token:")
        print("1. Message @BotFather in Telegram")
        print("2. Use /newbot command")
        print("3. Follow instructions to create bot")
        print("4. Copy token and add to .env file")
        return

    print("Starting Telegram bot...")
    print("Press Ctrl+C to stop")

    try:
        # Настраиваем бота
        telegram_bot.setup_bot(bot_token)

        # Запускаем бота
        telegram_bot.run_sync()

    except KeyboardInterrupt:
        print("\nBot stopped by user")
    except Exception as e:
        print(f"Error starting bot: {e}")

if __name__ == "__main__":
    main()